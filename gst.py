# gst.py
# Generalized Suffix Tree - Ukkonen's Algorithm
# Visualizer: https://brenden.github.io/ukkonen-animation/
#!! Inspiration: https://www.geeksforgeeks.org/ukkonens-suffix-tree-construction-part-1/

from __future__ import annotations  # type annotations
from operator import attrgetter     # used to determine equality of nodes
import string as stringlib          # access sets of strings for alphabet creation

# Global variables
TERMINAL: str   = stringlib.ascii_uppercase # Size limits the number of input words due to each needing a unique terminal
NONTERM:  str   = stringlib.ascii_lowercase # Letters allowed in words
ALPHABET: str   = TERMINAL + NONTERM #! ORDER MATTERS
LEAFEND:  int   = -1    # Required here so SuffixTree and SuffixTreeNode can access. Could be placed inside SuffixTree but then so would SuffixTreeNode, reducing usability and readability
DEBUG:    bool  = False # Enables debug prints highlighting computations and steps taken

def isValidWord(s: str) -> bool:
  '''Return whether the string is a valid word'''
  global NONTERM
  for c in s:
    if c not in NONTERM:
      return False
  return True

def isInAlphabet(s: str) -> bool:
  '''Return whether all characters in s are within the alphabet'''
  global ALPHABET
  for c in s:
    if c not in ALPHABET:
      return False
  return True


class SuffixNodeReference:
  '''Data structure for optional suffix node reference. Enforces type requirements'''
  def __set_name__(self: SuffixNodeReference, owner: any, name: str) -> None:
    self._name = name

  def __get__(self: SuffixNodeReference, instance: any, owner: any) -> SuffixTreeNode | None:
    '''Retrieve the referenced node or None if it does not exist'''
    # instance is the particular instance that is calling __get__
    # owner is the class with this descriptor (what *class* contains this SuffixNodeReference instance)
    return instance.__dict__[self._name]

  def __set__(self: SuffixNodeReference, instance: any, value: any) -> None:
    '''Set or remove a node reference'''
    if not isinstance(value, SuffixTreeNode) and value != None:
      raise ValueError(f'{self._name} must be a SuffixTreeNode or None, {type(value)}') from None
    instance.__dict__[self._name] = value


class SuffixNodeDict(dict):
  '''Data structure for enforcing proper references to suffix node children'''
  def __missing__(self: SuffixNodeDict, key: any) -> None:
    '''Return no node if the requested edge does not have a child'''
    return None

  def __getitem__(self: SuffixNodeDict, key: any) -> SuffixTreeNode | None:
    '''Retrieve the referenced node or None if it does not exist. Enforces retrieving only edges within the alphabet'''
    if not isinstance(key, str) or not isInAlphabet(key) and len(key) == 1:
      raise IndexError(f'edges must be characters within the alphabet, {key}')
    return super().__getitem__(key)

  def __setitem__(self: SuffixNodeDict, key: any, value: any) -> None:
    '''Set or remove a referenced node. Enforces only setting edges within the alphabet'''
    if not isinstance(key, str) or not isInAlphabet(key) and len(key) == 1:
      raise IndexError(f'edges must be characters within the alphabet, {key}')
    if value == None:
      # Setting to None is equivalent to removing it due to having a __missing__ method
      if key in self:
        super().__delitem__(key)
      return
    if not isinstance(value, SuffixTreeNode):
      raise ValueError(f'child must be a SuffixTreeNode or None, got {type(value)}') from None
    return super().__setitem__(key, value)

  @property
  def size(self: SuffixNodeDict) -> int:
    '''Return the number of child nodes'''
    return len([v for k, v in self.items() if v != None])


class SuffixTreeNode:

  # Initialize here to allow type checking
  suffixLink: SuffixNodeReference = SuffixNodeReference()

  def __init__(self: SuffixTreeNode, leaf: bool, start: int, end: int | None = None, id: int = -1) -> SuffixTreeNode:
    '''Create a suffix tree node for string S'''
    global ALPHABET
    self._id:           int                   = id # ID to identify instances during printing
    self.start:         int                   = start
    # For leaves end must be equal to last tree position. leaf = True indicates a leaf
    self._end:          int | None            = end
    self.leaf:          bool                  = leaf
    # Index of suffix in path from root to leaf. Non-leaves = -1
    self.suffixIndex:   int                   = -1
    # Node references
    self._children:     SuffixNodeDict        = SuffixNodeDict() # due to collections being by reference, cannot instantiate like suffixLink and need to use another, separate structure
    self.suffixLink                           = None

  def __repr__(self: SuffixTreeNode) -> str:
    '''Get string representation of this node'''
    return f'STNode(id={self._id}, pos={self.start}:{self.end}, c={self.children.size}, i={self.suffixIndex})'

  def __eq__(self: SuffixTreeNode, other: any) -> bool:
    '''Compare this node for equality to another object'''
    if not isinstance(other, SuffixTreeNode):
      return False
    atg = attrgetter('start', '_end', 'suffixLink')
    return atg(self) == atg(other)

  def __ne__(self: SuffixTreeNode, other: any) -> bool:
    '''Compare this node for inequality to another object'''
    if not isinstance(other, SuffixTreeNode):
      return True
    atg = attrgetter('start', '_end', 'suffixLink')
    return atg(self) != atg(other)

  @property
  def end(self: SuffixTreeNode) -> int:
    '''Get the end index of this node'''
    # Check if _end is set. Cannot rely on leaf because we may set end manually during tree tidy
    if self._end == None:
      global LEAFEND
      return LEAFEND
    return self._end

  @end.setter
  def end(self: SuffixTreeNode, val: any) -> None:
    '''Set the end index of this node'''
    # if self.isLeaf():
    #   raise Exception('Leaf node end is read-only')
    if not isinstance(val, int):
      raise Exception(f'Unexpected type for end value, {type(val)}')
    self._end = val

  @property
  def children(self: SuffixTreeNode) -> SuffixNodeDict:
    '''Children of this suffix node. Read-only'''
    return self._children

  @property
  def edgeLength(self: SuffixTreeNode) -> int:
    '''Edge length of the path of this node. Read-only'''
    return (self.end - self.start + 1)

  def isLeaf(self: SuffixTreeNode) -> bool:
    '''Whether this node is a leaf'''
    return self.leaf

  def isOutgoingEdge(self: SuffixTreeNode) -> bool:
    '''Whether this node has any outgoing edges'''
    return (self.children.size > 0)


class SuffixTree:

  def __init__(self: SuffixTree, strings: list[str]) -> SuffixTree:
    '''Initialize and create a suffix tree from the input string'''
    global TERMINAL
    if (len(strings) > len(TERMINAL)):
      raise Exception(f'Too many words given, maximum is {len(TERMINAL)}')
    for i, string in enumerate(strings):
      if not isValidWord(string):
        raise Exception(f'Input string \'{string}\' has invalid characters')
      if string[-1] not in TERMINAL:
        string += TERMINAL[i]
        print(f'Adding terminal, new string is \'{string.replace(TERMINAL[i], "$")}\'')
        strings[i] = string

    self._string: str             = strings # Store string representation
    self._size:   int             = len(self.string) # Size of input string (excluding terminal)
    self._count:  int             = 0 # Number of nodes in the tree
    self.root:    SuffixTreeNode  = self._createRoot() # Tree root node (start = end = -1)

    # Algorithm components
    self.aNode:                   SuffixTreeNode = self.root  # Active node (where traversal starts for an extension)
    self.aEdge:                   int = -1                    # Active edge (which character is next during traversal)
    self.aLength:                 int = 0                     # Active length (how far we need to walk down during traversal)
    self._remaining_suffix_count: int = 0                     # Remaining suffix count (how many suffixes need to be added)

    # Printing components (do not effect functionality but help print state)
    self._phase: int = -1 # Current phase

    self._createSuffixTree()

  @property
  def string(self: SuffixTree) -> str:
    '''String syntax tree represents. Read-only'''
    return ''.join(self._string)

  @property
  def numstring(self: SuffixTree) -> int:
    '''Number of strings in tree. Read-only'''
    return len(self._string)

  @property
  def aEdgeChar(self: SuffixTree) -> str:
    '''Get character at active edge. Read-only'''
    return self.string[self.aEdge]

  @property
  def count(self: SuffixTree) -> int:
    '''Number of nodes used by the suffix tree. Read-only'''
    return self._count # fix now we delete the terminal nodes, this will be incorrect

  def charAt(self: SuffixTree, i: int) -> str:
    '''Get active character'''
    return self.string[i]

  def _debugPrint(self: SuffixTree, s: str) -> None:
    global DEBUG
    if not DEBUG:
      return
    print(s)

  def _debugPrintExtension(self: SuffixTree, n: int) -> None:
    self._debugPrint(f' == Extension {n}: \'{self.string[n-1:self._phase+1]}\' ({self._remaining_suffix_count} left after Rule 1) ==')

  def _debugPrintRule1Changes(self: SuffixTree, node: SuffixTreeNode, i: int) -> int:
    '''DEBUG ONLY: Print all Rule 1 extensions for debug logging. i is the number of extensions. Returns number of next extension for printing'''
    global ALPHABET
    # This only does anything when debug is enabled. Shortcut return if DEBUG is not enabled
    if not DEBUG:
      return 0

    # If node is empty, return
    if node == None:
      return i

    # If node is a leaf, it is updated to reflect the new lowest point
    if node.isLeaf():
      self._debugPrintExtension(i)
      self._debugPrint('Rule 1')
      return i + 1

    # Go through each child and print any Rule 1 changes
    for c in ALPHABET:
      child = node.children[c]
      i = self._debugPrintRule1Changes(child, i)

    # Return current extension number
    return i

  def _createSuffixTree(self: SuffixTree, pause: bool = False) -> None:
    '''Create the suffix tree'''
    # perform |S| extensions
    for i in range(self._size):
      # For each extension, the considered suffixes increase by 1
      self._extendSuffixTree(i)

      if (pause):
        self._debugPrint(f' ==== End of Phase {self._phase+1} State ====')
        self._debugPrint(f'Active Node:   {self.aNode}')
        self._debugPrint(f'Active Edge:   \'{self.aEdgeChar}\'/{self.aEdge}')
        self._debugPrint(f'Active Length: {self.aLength}')
        self._debugPrint(f'Suffixes Left: {self._remaining_suffix_count}')
        self.printSuffixTree(self.root)
        if (input('Enter \'q\' to stop: ').lower() == 'q'):
          break

    self._debugPrint(f' ===== Assigning Suffix Indicies =====')
    self._setSuffixIndexes(self.root, 0) #~ To match 1-indexing, start at 1

  def _extendSuffixTree(self: SuffixTree, pos: int) -> None:
    '''Perform the ith extension phase to the suffix tree'''

    # todo
    #? how exactly is last_new_node updated?

    # Extension Rule 1: Add new character to existing leaf node
      # Update final position on leaf node
    # Extension Rule 2: Create new Leaf node (and possibly internal node if label lands between edges)
      # Create new leaf node and update parent's child array
      # Create new internal node if necessary
    # Extension Rule 3: Current character is found on existing path being traversed
      # Do nothing
      # Stop current phase

    # Remaining Suffix Count tracks how many extensions are yet to be done EXPLICITLY
      # Implicit suffixes are those which are culminated by Extension Rule 3 (suffix exists in a path of a larger suffix)
      # If Remaining Suffix Count = 0 at end of a phase, then all suffixes are explicitly added
      # If Remaining Suffix Count != 0 at end of a phase, then there is at least one implicit suffix
      # and Rule 3 stopped us early. These implicit suffixes will be added in later phases when a unique
      # character is found on that path

    # Active Point: Storing locations in the Suffix Tree to inform later extensions and prevent
    # uneccessary traversal in the Suffix Tree, maintaining linear construction time
    # APCFER2C1: Change required for Rule 2, case 1 - activeNode is root and activeLength>0
      # Decrement activeLength by 1
      #? Set activeEdge to position `pos - _remaining_suffix_count + 1`
    # APCFER2C2: Change required for Rule 2, case 2 - activeNode is not root
      # Traverse suffix link from activeNode to get new activeNode
      #? Start next extension from there
    # APCFER3: Change required for Rule 3
      # Increment activeLength by 1
      # activeNode and activeEdge remain the same
    # APCFWD: Change required for walk down. activePoint may change depending on extension's final rule used
      # activePoint may also change during walk down. Update all 3 activePoint properties if
      # a internal node is hit so that activePoint points to the same location from new internal node
    # APCFALZ: Change required for activeLength of 0.
      # Next character we look for is current one being processed

    # Trick 1: Compress node edges so one node jump can pass many characters
      # Implemented through SuffixTreeNode's start and end properties
    # Trick 2: When Rule 3 applies, stop processing
      # If a suffix ends in the path of another suffix, it and all other suffixes of the current phase will end in that same path
    # Trick 3: For phase i, all leaf nodes will be of (start,i) then in phase i+1, they will be (start,i+1)
      # Once a leaf is created, it always stays a leaf and Rule 1 will always apply to it

    global LEAFEND
    self._phase = pos # update phase for printing

    self._debugPrint(f'========== Phase {pos+1} \'{self.string[pos]}\' / {[self.string[pos-i:pos+1] for i in range(pos, -1, -1)]} =========')

    #! TRICK 3
    LEAFEND = pos # All leaves track this value by reference so this performs all Rule 1 updates
    self._remaining_suffix_count += 1 # New suffix exists and needs to be added to the tree

    #! RULE 1 (add character to exisiting node)
    ext = self._debugPrintRule1Changes(self.root, 1) # Extension number for current phase

    last_new_node: SuffixTreeNode | None = None # Internal node waiting for suffix link update

    # Go until Rule 3 or all suffixes that need to be added are added
    while self._remaining_suffix_count > 0:
      # Print all non-Rule 1 suffixes required to be added
      self._debugPrintExtension(ext)
      ext += 1

      # Have we reached our node? If so, look at current character as the desired edge
      if self.aLength == 0:
        #! APCFALZ (aLength = 0)
        self._debugPrint('APCFALZ')
        self.aEdge = pos

      # aEdge transition from aNode does not exist
      if self.aNode.children[self.aEdgeChar] == None:
        #! RULE 2 (new leaf is created, not requiring another node be split)
        self._debugPrint('Rule 2 - No split')
        self.aNode.children[self.aEdgeChar] = self._createNode(True, pos)

        # If internal node was made before, update suffix link to active node
        if last_new_node != None:
          last_new_node.suffixLink = self.aNode
          last_new_node = None

      # aEdge transition from aNode exists
      else:
        # Get next node from active node taking active edge transition
        next_node = self.aNode.children[self.aEdgeChar]
        # See if aLength brings us to or past the next node
        #! TRICK 1
        if self._walkDownTree(next_node):
          # Start extension from new activePoint and restart this iteration
          continue

        if self.string[next_node.start + self.aLength] == self.string[pos]:
          #! Rule 3 (current character being processed is on edge)
          self._debugPrint('Rule 3')
          # Update internal node suffix link
          if last_new_node != None and self.aNode != self.root:
            last_new_node = self.aNode
            last_new_node = None
          #! APCFER3
          self._debugPrint('APCFER3')
          self.aLength += 1
          #! TRICK 2
          break

        #! Rule 2 (new leaf node requiring splitting of an internal node)
        self._debugPrint('Rule 2 - Split')

        # We have fallen off the tree and must create a new internal node to contain the new node
        split_end = next_node.start + self.aLength - 1 # new end position for split

        split_node = self._createNode(False, next_node.start, split_end) # new internal node
        self.aNode.children[self.aEdgeChar] = split_node # update active node child to point to new node

        split_node.children[self.string[pos]] = self._createNode(True, pos) # new leaf out from split node

        next_node.start += self.aLength # push updated node's start past the new node
        # split_node.children[self.aEdgeChar] = next_node # update child of split node with edge of next_node's first char
        split_node.children[self.charAt(next_node.start)] = next_node # update child of split node with edge of next_node's first char

        # Update previous internal node if needed
        if last_new_node != None:
          last_new_node.suffixLink = split_node

        # New internal node is missing its suffix link (currently pointing to root)
        # We need to update the suffix link to any new internal internal nodes created
        last_new_node = split_node

      # A suffix got added to the tree, decrement number of suffixes to be added
      self._remaining_suffix_count -= 1
      if self.aNode == self.root and self.aLength > 0:
        #! APCFER2C1
        self._debugPrint('APCFER2C1')
        self.aLength -= 1
        self.aEdge = pos - self._remaining_suffix_count + 1
      elif self.aNode != self.root:
        #!APCFER2C2
        self._debugPrint('APCFER2C2')
        self.aNode = self.aNode.suffixLink
        assert(self.aNode != None)

  def _walkDownTree(self: SuffixTree, node: SuffixTreeNode) -> bool:
    # Walk down node depending on activePoint
    if self.aLength >= node.edgeLength:
      #! APCFWD
      self._debugPrint('APCFWD')
      # Update all active components
      self.aEdge += node.edgeLength # next character
      self.aLength -= node.edgeLength
      self.aNode = node
      assert(self.aNode != None)
      return True
    return False

  def _nextID(self: SuffixTree) -> int:
    self._count += 1
    return self._count-1

  def _createRoot(self: SuffixTree) -> SuffixTreeNode:
    '''Create and return a new root node'''
    node = SuffixTreeNode(False, -1, -1, self._nextID())
    node.suffixLink = node
    node.suffixIndex = -1
    return node

  def _createNode(self: SuffixTree, leaf: bool, start: int, end: int | None = None) -> SuffixTreeNode:
    '''Create and return a node with specified start and end indicies'''
    if not isinstance(leaf, int):
      raise Exception(f'Unexpected type for leaf, {type(start)}')
    if not isinstance(start, int):
      raise Exception(f'Unexpected type for start index, {type(start)}')
    if not isinstance(end, int) and end != None:
      raise Exception(f'Unexpected type for end index, {type(end)}')

    # Create new node
    node = SuffixTreeNode(leaf, start, end, self._nextID())
    # Set defaults
    node.suffixLink = self.root # all links go to root. Might get updated with other nodes during execution
    node.suffixIndex = -1 # internal node by default. Update at end
    return node

  def _setSuffixIndexes(self: SuffixTree | None, node: SuffixTreeNode, labelHeight: int) -> None:
    '''Sets the suffix index for each leaf node in the tree. Internal nodes keep their default index. Done using DFS'''
    global ALPHABET
    if node == None:
      return

    if node != self.root:
      self._debugPrint(self.getSubstringFromNode(node))

    leaf = True
    for c in ALPHABET:
      child = node.children[c]
      # Check for any children
      if child != None:
        if leaf and node.start != -1:
          self._debugPrint(f' [{node.suffixIndex}]')

        # A child exists, so update that this node is not a leaf and recurse on that child
        leaf = False
        self._setSuffixIndexes(child, labelHeight + child.edgeLength)

    if leaf:
      # This node has no children, so update its suffix index
      node.suffixIndex = self._size - labelHeight
      self._debugPrint(f' [{node.suffixIndex}]')

  def getSubstring(self: SuffixTree, i: int, j: int) -> str:
    '''Get a substring of the input string based on start and stop indicies (inclusive). Replaces all end-of-word terminals with $'''
    global TERMINAL
    string = ""
    # Check if root since range(-1, 0) results in [-1] which will be an end of word terminal which is not technically correct
    if i == -1 and j == -1:
      return string
    # Splice the part of the string we want
    string = self.string[i:j+1]
    # Replace all terminals
    for termnum in range(self.numstring):
      string = string.replace(TERMINAL[termnum], '$')
    return string

  def getSubstringFromNode(self: SuffixTree, node: SuffixTreeNode) -> str:
    '''Get a substring from a suffix tree node'''
    return self.getSubstring(node.start, node.end)

  def printSuffixTree(self: SuffixTree, node: SuffixTreeNode | None, indent: int = 0) -> None:
    '''Print the suffix tree as a simplified tree. Done using DFS'''
    global ALPHABET
    if node == None:
      return

    print('\t' * indent + f'\'{self.getSubstringFromNode(node)}\', {node} -> ', end='')
    link = node.suffixLink
    if link == self.root:
      print(f'ROOT') # shorthand for root
    elif link != None:
      print(f'\'{self.getSubstringFromNode(link)}\', {link}')
    else:
      print(f'None')

    for c in ALPHABET:
      child = node.children[c]
      self.printSuffixTree(child, indent + 1)

  def _getSuffixArray(self: SuffixTree, node: SuffixTreeNode | None, lst: list[str] | None = None) -> list[str]:
    '''Recursive function to build suffix array in lst'''
    global ALPHABET
    # If node is empty, return input list
    if node == None:
      return lst

    # Check if list was given. If not, make an empty one
    # Do not give default value 'lst = []' in method declaration because Python is weird about that
    if lst == None:
      lst = []

    # Add self if you have a suffix index
    if node.isLeaf(): # same as suffixIndex() >= 0
      lst.append(node.suffixIndex)

    # Add each child to lst
    for c in ALPHABET:
      child = node.children[c]
      lst = self._getSuffixArray(child, lst)

    return lst

  def getSuffixArray(self: SuffixTree) -> list[int]:
    '''Returns the suffix array for the suffix tree'''
    return self._getSuffixArray(self.root)

  def getStringSuffixArray(self: SuffixTree) -> list[str]:
    '''Returns the suffixes that make up the suffix array'''
    return [self.string[pos:] for pos in self.getSuffixArray()]

  def getInverseSuffixArray(self: SuffixTree) -> list[int]:
    '''Returns the suffix array for the suffix tree'''

    sa = self.getSuffixArray()
    isa = [0] * len(sa)
    for ind, pos in enumerate(sa):
      isa[pos] = ind
    return isa

  def getLCPArray(self: SuffixTree) -> list[int]:
    '''Returns the LCP array. Uses Kasai's algorithm'''
    sa = self.getSuffixArray()
    isa = self.getInverseSuffixArray()
    lcp: list[int] = [0] * len(sa)

    l = 0
    for i in range(self._size-1):
      k = isa[i]
      j = sa[k-1] # j = phi(i)
      while self.string[i+l] == self.string[j+l]:
        l += 1
      lcp[k] = l
      if l > 0:
        l -= 1
    return lcp

  def _tidyTree(self: SuffixTree, node: SuffixTreeNode) -> None:
    if node == None:
      return

    if not node.isLeaf():
      for c, child in node.children.items():
        self._tidyTree(child)

    else:
      front_word = self.getSubstringFromNode(node).split('$')[0] # Remove all characters after the first terminal
      node.end = node.start + len(front_word)

    # Remove all but one of the terminal
    # todo will this hurt SA/LCP calc b/c we are removing elements?
    keep = True
    for termnum in range(self.numstring):
      if keep:
        if node.children[TERMINAL[termnum]] != None:
          keep = False
      else:
        node.children[TERMINAL[termnum]] = None

  def tidyTree(self: SuffixTree) -> None:
    '''Cleans the suffix tree to prevent suffix nodes from being cluttered due to the handling of multiple words'''
    global TERMINAL
    self._tidyTree(self.root)




if __name__ == '__main__':
  print(f'Alphabet: {ALPHABET}')

  string = input('Enter a string to compute GST of: ').split(' ')
  # string = ['abbc']
  # string = ['abcabxabcd']
  # string = ['geeksforgeeks']
  # string = ['good']
  # string = ['gatagaca']
  # string = ['atcgatcga', 'atcca', 'gaak']
  # string = ['gaakak', 'gaakab']

  tree = SuffixTree(string)

  print(f' == String \'{tree.string}\' ==')
  print(f"# Nodes = {tree.count}")

  print(f' == Suffix Tree ==')
  tree.printSuffixTree(tree.root)

  print(f' == Tidied Tree ==')
  tree.tidyTree()
  tree.printSuffixTree(tree.root)

  print(f' == Metadata Arrays ==')
  print(f'Suffix Array: {tree.getSuffixArray()}')
  print(f'Str.S. Array: {tree.getStringSuffixArray()}')
  print(f'Inv Suffix:   {tree.getInverseSuffixArray()}')
  print(f'LCP Array:    {tree.getLCPArray()}')
