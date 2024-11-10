# gst.py
# Generalized Suffix Tree - Ukkonen's Algorithm
# Visualizer: https://brenden.github.io/ukkonen-animation/
#!! Inspiration: https://www.geeksforgeeks.org/ukkonens-suffix-tree-construction-part-1/

from __future__ import annotations  # type annotations
from operator import attrgetter     # used to determine equality of nodes
import string as stringlib          # access sets of strings for alphabet creation

# Global variables
TERMINAL: str   = '$'
LEAFEND:  int   = -1  # Required so SuffixTree and SuffixTreeNode can access. Could be placed inside SuffixTree but then so would SuffixTreeNode, reducing usability and readability
DEBUG:    bool  = False

class SuffixTreeNode:

  Alphabet: str = TERMINAL + stringlib.ascii_lowercase #! ORDER MATTERS

  @staticmethod
  def isInAlphabet(s: str) -> bool:
    '''Return whether all characters in s are within the alphabet'''
    for c in s:
      if c not in SuffixTreeNode.Alphabet:
        return False
    return True

  def __init__(self: SuffixTreeNode, leaf=False) -> SuffixTreeNode:
    '''Create a suffix tree node for string S'''
    # Dict for determing which child depending on first char in label
    self._children:     dict[str, SuffixTreeNode | None] = {c: None for c in SuffixTreeNode.Alphabet}
    self._parent:       SuffixTreeNode        = None
    self._numchildren:  int                   = 0
    self._suffixLink:   SuffixTreeNode | None = None
    self._start:        int                   = 0
    # For leaves, end must be equal to last tree position
    self._end:          int                   = -1
    self._leaf:         bool                  = leaf # once a leaf, always a leaf
    # index of suffix in path from root to leaf. Non-leaves = -1
    self._suffixIndex:  int                   = -1

  def __repr__(self: SuffixTreeNode) -> str:
    '''Get string representation of this node'''
    return f'SuffixTreeNode({self.start}:{self.end}, children={self.getNumChildren()})'

  def __eq__(self: SuffixTreeNode, other: any) -> bool:
    '''Compare this node for equality to another object'''
    if type(other) not in (SuffixTreeNode,):
      return False
    atg = attrgetter('_start', '_end', '_suffixLink')
    return atg(self) == atg(other)

  def __ne__(self: SuffixTreeNode, other: any) -> bool:
    '''Compare this node for inequality to another object'''
    if type(other) not in (SuffixTreeNode,):
      return False
    atg = attrgetter('_start', '_end', '_suffixLink')
    return atg(self) != atg(other)

  @property
  def end(self: SuffixTreeNode) -> int:
    '''Get the end index of this node'''
    if self.isLeaf() == True:
      global LEAFEND
      return LEAFEND
    return self._end

  @end.setter
  def end(self: SuffixTreeNode, val: int) -> None:
    '''Set the end index of this node'''
    if self.isLeaf():
      raise Exception('Leaf nodes cannot be manually updated')
    if type(val) not in (int,):
      raise Exception(f'Unexpected type for end value, {type(val)}')
    self._end = val

  @property
  def start(self: SuffixTreeNode) -> int:
    '''Get the start index of this node'''
    return self._start

  @start.setter
  def start(self: SuffixTreeNode, val: int) -> None:
    '''Set the start index of this node'''
    if type(val) not in (int,):
      raise Exception(f'Unexpected type for start value, {type(val)}')
    self._start = val

  def getSuffixLink(self: SuffixTreeNode) -> SuffixTreeNode | None:
    '''Get suffix link for this node'''
    return self._suffixLink

  def setSuffixLink(self: SuffixTreeNode, node: SuffixTreeNode | None, allow_none: bool = False) -> None:
    '''Set suffix link for this node'''
    if type(node) not in (SuffixTreeNode,) and (type(node) in (None,) and not allow_none):
      raise Exception(f'Unexpected type for suffix link, {type(node)}')
    self._suffixLink = node

  # def getSuffixIndex(self: SuffixTreeNode) -> int:
  #   return self._suffixIndex

  # def setSuffixIndex(self: SuffixTreeNode, i: int) -> None:
  #   if type(i) not in (int,):
  #     raise Exception(f'Unexpected type for suffix index, {type(i)}')
  #   self._suffixIndex = i

  def getChild(self: SuffixTreeNode, c: str) -> SuffixTreeNode | None:
    '''Get a child for a specific edge'''
    if type(c) not in (str,):
      raise Exception(f'Unexpected type for key, {type(c)}')
    if not SuffixTreeNode.isInAlphabet(c):
      raise Exception(f'Input character \'{c}\' not in alphabet')

    return self._children[c]

  def setChild(self: SuffixTreeNode, c: str, node: SuffixTreeNode | None) -> None:
    '''Set child node for a specific edge for this node'''
    if type(c) not in (str,):
      raise Exception(f'Unexpected type for key, {type(c)}')
    if type(node) not in (SuffixTreeNode, ) and node is not None:
      raise Exception(f'Unexpected type for child node, {type(node)}')
    if not SuffixTreeNode.isInAlphabet(c):
      raise Exception(f'Input character \'{c}\' not in alphabet')

    # Update number of children
    if node == None and self.getChild(c) != None:
      self._numchildren -= 1
    elif node != None and self.getChild(c) == None:
      self._numchildren += 1

    self._children[c] = node
    # Update parent node to point to this node
    if node is not None:
      node.setParent(self)

  def getParent(self: SuffixTreeNode) -> SuffixTreeNode:
    '''Get this node's parent'''
    return self._parent

  def setParent(self: SuffixTreeNode, parent: SuffixTreeNode) -> None:
    '''Set the parent of this node'''
    if type(parent) not in (SuffixTreeNode,):
      raise Exception(f'Unexpected type for parent, {type(parent)}')
    self._parent = parent

  def getNumChildren(self: SuffixTreeNode) -> int:
    '''Return the number of children this node has'''
    return self._numchildren

  def getEdgeLength(self: SuffixTreeNode) -> int:
    '''Get length of the path of this node'''
    return (self.end - self.start + 1)

  def isRoot(self: SuffixTreeNode) -> bool:
    '''Get whether this node is a root node'''
    return (self.start == -1 and self.end == -1)

  def isLeaf(self: SuffixTreeNode) -> bool:
    '''Get whether this node is a leaf'''
    return self._leaf

  def isInternal(self: SuffixTreeNode) -> bool:
    '''Get whether this node is an internal (non-leaf) node'''
    return not self.isLeaf()

  def isOutgoingEdge(self: SuffixTreeNode) -> bool:
    '''Get whether this node has any outgoing edges'''
    return (self._numchildren > 0)

  def getChildren(self: SuffixTreeNode) -> list[str]:
    '''DEBUG ONLY: Return all non-empty children'''
    global DEBUG
    if not DEBUG:
      raise Exception('Method only permitted during debug')
    return list(filter(lambda k : self._children[k] != None, self._children))

  def delChild(self: SuffixTreeNode, c: str) -> None:
    '''DEBUG ONLY: Delete a specific child'''
    global DEBUG
    if not DEBUG:
      raise Exception('Method only permitted during debug')
    del self._children[c]


class SuffixTree:
  def __init__(self: SuffixTree, string: str) -> SuffixTree:
    '''Initialize and create a suffix tree from the input string'''
    if not SuffixTreeNode.isInAlphabet(string):
      raise Exception(f'Input string \'{string}\' not in alphabet')
    if string[-1] != TERMINAL:
      string += TERMINAL
      print(f'Adding terminal, new string is \'{string}\'')

    self._string: str             = string # Store string representation
    self._size:   int             = len(self.string) # Size of input string
    self._count:  int             = 0 # Number of nodes in the tree
    self.root:    SuffixTreeNode  = self._createRoot() # Tree root node (start = end = -1)

    # Algorithm components
    LEAFEND = 0 # captured by contained nodes
    # Active node (where traversal starts for an extension)
    self.aNode:                   SuffixTreeNode = self.root
    # Active edge (which character is next during traversal)
    self.aEdge:                   int = -1
    # Active length (how far we need to walk down during traversal)
    self.aLength:                 int = 0
    # Remaining suffix count. How many suffixes need to be added
    self._remaining_suffix_count: int = 0

    # Printing components (do not effect functionality but help print state)
    self._phase: int = -1 # Current phase

    self._createSuffixTree()

  @property
  def string(self: SuffixTree) -> str:
    '''Get string syntax tree represents'''
    return self._string

  @property
  def aEdgeChar(self: SuffixTree) -> str:
    '''Get active character'''
    return self.string[self.aEdge]

  @aEdgeChar.setter
  def aEdgeChar(self: SuffixTree, offset: int) -> None:
    '''Shift aEdge by offset'''
    if self.aEdge+offset < 0 or self.aEdge+offset >= self._size:
      raise Exception(f'aEdge shift out of bounds, 0<={self.aEdge+offset}<{self._size} doesn\'t hold')
    self.aEdge += offset

  @property
  def count(self: SuffixTree) -> int:
    return self._count

  def _debugPrint(self: SuffixTree, s: str) -> None:
    global DEBUG
    if not DEBUG:
      return
    print(s)

  def debugPrintExtension(self: SuffixTree, n: int) -> None:
    self._debugPrint(f' == Extension {n}: \'{self.string[n-1:self._phase+1]}\' ({self._remaining_suffix_count} left after Rule 1) ==')

  def charAt(self: SuffixTree, i: int) -> str:
    '''Get active character'''
    return self.string[i]

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
    ext = self.printRule1Changes(self.root, 1) # Extension number for current phase

    last_new_node: SuffixTreeNode | None = None # Internal node waiting for suffix link update

    # Go until Rule 3 or all suffixes that need to be added are added
    while self._remaining_suffix_count > 0:
      # Print all non-Rule 1 suffixes required to be added
      self.debugPrintExtension(ext)
      ext += 1

      # Have we reached our node? If so, look at current character as the desired edge
      if self.aLength == 0:
        #! APCFALZ (aLength = 0)
        self._debugPrint('APCFALZ')
        self.aEdge = pos

      # aEdge transition from aNode does not exist
      if self.aNode.getChild(self.aEdgeChar) == None:
        #! RULE 2 (new leaf is created, not requiring another node be split)
        self._debugPrint('Rule 2 - No split')
        self.aNode.setChild(self.aEdgeChar, self._createNode(pos))

        # If internal node was made before, update suffix link to active node
        if last_new_node != None:
          last_new_node.setSuffixLink(self.aNode)
          last_new_node = None

      # aEdge transition from aNode exists
      else:
        # Get next node from active node taking active edge transition
        next_node = self.aNode.getChild(self.aEdgeChar)
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
            last_new_node.setSuffixLink(self.aNode)
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

        split_node = self._createNode(next_node.start, split_end) # new internal node
        self.aNode.setChild(self.aEdgeChar, split_node) # update active node child to point to new node

        split_node.setChild(self.string[pos], self._createNode(pos)) # new leaf out from split node

        next_node.start += self.aLength # push updated node's start past the new node
        split_node.setChild(self.charAt(next_node.start), next_node) # update child of split node with edge of next_node's first char

        # Update previous internal node if needed
        if last_new_node != None:
          last_new_node.setSuffixLink(split_node)

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
        self.aNode = self.aNode.getSuffixLink()

  def _walkDownTree(self: SuffixTree, node: SuffixTreeNode) -> bool:
    # Walk down node depending on activePoint
    if self.aLength >= node.getEdgeLength():
      #! APCFWD
      self._debugPrint('APCFWD')
      # Update all active components
      self.aEdge += node.getEdgeLength() # next character
      self.aLength -= node.getEdgeLength()
      self.aNode = node
      return True
    return False

  def _createRoot(self: SuffixTree) -> SuffixTreeNode:
    '''Create and return a new root node'''
    self._count += 1
    node = SuffixTreeNode(False)
    node.start = -1
    node.end = -1
    node.setSuffixLink(node)
    return node

  def _createNode(self: SuffixTree, start: int, end: int | None = None) -> SuffixTreeNode:
    '''Create and return a node with specified start and end indicies'''
    if type(start) not in (int,):
      raise Exception(f'Unexpected type for start index, {type(start)}')
    if type(end) not in (int,) and end != None:
      raise Exception(f'Unexpected type for end index, {type(end)}')

    # Update our state
    self._count += 1
    leaf = end == None
    # Create new node
    node = SuffixTreeNode(leaf)
    # Assign state
    node.start = start
    if not leaf:
      node.end = end
    # Set defaults
    # node.setSuffixIndex(-1) # internal node
    return node

  def getSubstring(self: SuffixTree, i: int, j: int) -> str:
    string = ""
    for k in range(i, j+1):
      string += self.string[k]
    return string

  def getSubstringFromNode(self: SuffixTree, node: SuffixTreeNode) -> str:
    return self.getSubstring(node.start, node.end)

  def getSuffix(self: SuffixTree, j: int) -> str:
    return self.string[j:]

  def getSuffixFromNode(self: SuffixTree, node: SuffixTreeNode) -> str:
    return self.getSuffix(node.start)

  def getPathString(self: SuffixTree, node: SuffixTreeNode) -> str:
    '''Print entire label path from root to node'''
    string = ""
    while node != None:
      string = self.getSubstringFromNode(node) + string
      node = node.getParent()
    # if string == '': # root will have empty string due to -1 start and end
    #   string = self.string[-1]
    return string

  def _getSuffixArray(self: SuffixTree, node: SuffixTreeNode | None, lst: list[str] | None = None) -> list[str]:
    '''Recursive function to build suffix array in lst'''
    # Check if list was given. If not, make an empty one
    # Do not give default value 'lst = []' in method declaration because Python is weird about that
    if lst == None:
      lst = []

    # If node is empty, return input list
    if node == None:
      return lst

    # Add self
    lst.append(self.getSuffixFromNode(node))

    # Add each child to lst
    for c in SuffixTreeNode.Alphabet:
      child = node.getChild(c)
      lst = self._getSuffixArray(child, lst)

    return lst

  def getSuffixArray(self: SuffixTree) -> list[str]:
    '''Returns the suffix array for the suffix tree'''
    return self._getSuffixArray(self.root)

  def printSuffixArray(self: SuffixTree) -> None:
    '''Returns the suffix array for the suffix tree'''
    sa = self.getSuffixArray()
    for i, suffix in enumerate(sa):
      print(f'{i}: {suffix}')

  def printRule1Changes(self: SuffixTree, node: SuffixTreeNode, i: int) -> int:
    '''DEBUG ONLY: Print all Rule 1 extensions for debug logging. i is the number of extensions.'''
    # This only does anything when debug is enabled. Shortcut return if DEBUG is not enabled
    if not DEBUG:
      return 0

    # If node is empty, return
    if node == None:
      return i

    # If node is a leaf, it is updated to reflect the new lowest point
    if node.isLeaf():
      self.debugPrintExtension(i)
      self._debugPrint('Rule 1')
      return i + 1

    # Go through each child and print any Rule 1 changes
    for c in SuffixTreeNode.Alphabet:
      child = node.getChild(c)
      i = self.printRule1Changes(child, i)

    # Return current extension number
    return i

  def printSuffixTree(self: SuffixTree, node: SuffixTreeNode | None, indent: int = 0) -> None:
    '''Print the suffix tree as a simplified tree'''
    if node == None:
      return

    print('\t' * indent + f'{node}, label=\'{self.getSubstringFromNode(node)}\'')

    for c in SuffixTreeNode.Alphabet:
      child = node.getChild(c)
      self.printSuffixTree(child, indent + 1)


# _testSuffixTreeNode()
if __name__ == '__main__':
  print(f'Alphabet: {SuffixTreeNode.Alphabet}')


  string = 'abbc'
  # string = 'abcabxabcd'

  tree = SuffixTree(string)

  print(f' == String \'{tree.string}\' ==')
  print(f"# Nodes = {tree.count}")
  print(f' == Suffix Tree ==')
  tree.printSuffixTree(tree.root)
  print(f' == String \'{tree.string}\' ==')
  print(tree.getSuffixArray())
  tree.printSuffixArray()
