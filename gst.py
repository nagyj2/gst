#!/usr/bin/env python3
# Generalized Suffix Tree - Ukkonen's Algorithm
# Visualizer: https://brenden.github.io/ukkonen-animation/
#!! Inspiration: https://www.geeksforgeeks.org/ukkonens-suffix-tree-construction-part-1/

from __future__ import annotations  # type annotations
from operator import attrgetter     # used to determine equality of nodes
import string as stringlib          # access sets of strings for alphabet creation
import argparse                     # handling command line arguments

# Global variables
TERMINAL: str   = stringlib.ascii_uppercase # Size limits the number of input words due to each needing a unique terminal
ALPHABET: str   = stringlib.ascii_lowercase # Letters allowed in words
SYMBOLS:  str   = TERMINAL + ALPHABET #! ORDER MATTERS
LEAFEND:  int   = -1    # Required here so _SuffixTree and SuffixTreeNode can access. Could be placed inside _SuffixTree but then so would SuffixTreeNode, reducing usability and readability
DEBUG:    bool  = False # Enables walkthrough prints highlighting computations and steps taken

# Validate settings
assert not set(TERMINAL).intersection(set(ALPHABET)), f'There must be no overlap between alphabet and terminal characters'

def isValidWord(s: str) -> bool:
  '''Return whether the string is a valid word'''
  global ALPHABET
  for c in s:
    if c not in ALPHABET:
      return False
  return True

def isInAlphabet(s: str) -> bool:
  '''Return whether all characters in s are within the alphabet'''
  global SYMBOLS
  for c in s:
    if c not in SYMBOLS:
      return False
  return True

def _printSuffixTree(refstring: str, node: SuffixTreeNode, indent: list[bool], string: str) -> str:
  global TERMINAL

  # tidy replaces any terminals in the string with the corresponding $# for that terminal
  # purposefully stupid. Look to SuffixTree._printSuffixTree for an easier to understand implementation of the tree print
  tidy = lambda s : ''.join([(c if len(t) == 0 else f'${t[0][0]}') for c, t in tuple(map(lambda c: (c, tuple(filter(lambda i_t : i_t[1] == True, map(lambda i_t : (i_t[0], c == i_t[1]), tuple(enumerate(TERMINAL)))))), tuple(s)))])

  # substring returns the substring corresponding to the node's start and end position
  substring = lambda s, e : refstring[s:e+1]

  # strnode returns a string representation of a node without its suffix link
  strnode = lambda n : f'{tidy(substring(n.start, n.end))} [{n.id}]' + (f' ({n.suffixIndex})' if n.isLeaf() else '')

  # strnode_link returns a string representation of a node with its suffix link
  strnode_link = lambda n : strnode(n) + (' -> ' + strnode(n.suffixLink) if n.suffixLink and not n.suffixLink.isRoot() else '')

  if node == None:
    return string

  # Print this element
  string += f'* ' + strnode_link(node) + '\n'
  count = len(node.children.items())
  indent.append(True)
  for c, child in node.children.items():
    count -= 1
    if count == 0: # dont show vertical bar for last entry
        indent[-1] = False
    string += ''.join(['|   ' if b == True else '    ' for b in indent[:-1]]) + f'|\n'
    string += ''.join(['|   ' if b == True else '    ' for b in indent[:-1]]) + f'+---'
    string = _printSuffixTree(refstring, child, indent, string)

  indent.pop() # remove bar for this node
  return string

def stringSuffixTree(refstring: str, tree: SuffixTree) -> str:
  return _printSuffixTree(refstring, tree.root, [], '')

def _debugPrint(*args, **kwargs):
  global DEBUG
  if DEBUG:
    print(*args, **kwargs)


class _SuffixNodeReference:
  '''Data structure for optional suffix node reference. Enforces type requirements'''
  def __set_name__(self: _SuffixNodeReference, owner: any, name: str) -> None:
    self._name = name

  def __get__(self: _SuffixNodeReference, instance: any, owner: any) -> SuffixTreeNode | None:
    '''Retrieve the referenced node or None if it does not exist'''
    # instance is the particular instance that is calling __get__
    # owner is the class with this descriptor (what *class* contains this _SuffixNodeReference instance)
    return instance.__dict__[self._name]

  def __set__(self: _SuffixNodeReference, instance: any, value: any) -> None:
    '''Set or remove a node reference'''
    if not isinstance(value, SuffixTreeNode) and value != None:
      raise ValueError(f'{self._name} must be a SuffixTreeNode or None, {type(value)}') from None
    instance.__dict__[self._name] = value


class _SuffixNodeDict(dict):
  '''Data structure for enforcing proper references to suffix node children'''
  def __missing__(self: _SuffixNodeDict, key: any) -> None:
    '''Return no node if the requested edge does not have a child'''
    return None

  def __getitem__(self: _SuffixNodeDict, key: any) -> SuffixTreeNode | None:
    '''Retrieve the referenced node or None if it does not exist. Enforces retrieving only edges within the alphabet'''
    if not isinstance(key, str) or not isInAlphabet(key) and len(key) == 1:
      raise IndexError(f'edges must be characters within the alphabet, {key}')
    return super().__getitem__(key)

  def __setitem__(self: _SuffixNodeDict, key: any, value: any) -> None:
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
  def size(self: _SuffixNodeDict) -> int:
    '''Return the number of child nodes'''
    return len([v for k, v in self.items() if v != None])


class SuffixTreeNode:

  # Initialize here to allow type checking
  suffixLink: _SuffixNodeReference = _SuffixNodeReference()

  def __init__(self: SuffixTreeNode, leaf: bool, start: int, end: int | None = None, id: int = -1) -> SuffixTreeNode:
    '''Create a suffix tree node for string S'''
    global SYMBOLS
    self._id:           int                   = id # ID to identify instances during printing
    self.start:         int                   = start
    # For leaves end must be equal to last tree position. leaf = True indicates a leaf
    self._end:          int | None            = end
    self.leaf:          bool                  = leaf
    # Index of suffix in path from root to leaf. Non-leaves = -1
    self.suffixIndex:   int                   = -1
    # Node references
    self._children:     _SuffixNodeDict       = _SuffixNodeDict() # due to collections being by reference, cannot instantiate like suffixLink and need to use another, separate structure
    self.suffixLink                           = None

  def __repr__(self: SuffixTreeNode) -> str:
    '''Get string representation of this node'''
    return f'STNode(id={self.id}, pos={self.start}:{self.end}{"*" if self._end == None else ""}, c={self.children.size}, i={self.suffixIndex})'

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
  def id(self: SuffixTreeNode) -> int:
    '''ID of this node. Read-only'''
    return self._id

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
  def children(self: SuffixTreeNode) -> _SuffixNodeDict:
    '''Children of this suffix node. Read-only'''
    return self._children

  @property
  def edgeLength(self: SuffixTreeNode) -> int:
    '''Edge length of the path of this node. Read-only'''
    return (self.end - self.start + 1)

  def isRoot(self: SuffixTreeNode) -> bool:
    '''Whether this node is a root node'''
    return self.start == -1 and self.end == -1

  def isLeaf(self: SuffixTreeNode) -> bool:
    '''Whether this node is a leaf'''
    return self.leaf


class _SuffixTree:
  '''Suffix Tree Model Object. Holds data and handles queries'''
  def __init__(self: _SuffixTree, string: str) -> _SuffixTree:
    '''Initialize and create a suffix tree from the input string'''
    self._string: str             = string # Store string representation
    self._size:   int             = len(self._string) # Size of input string (excluding terminal)
    self._count:  int             = 0 # Number of nodes in the tree
    self.root:    SuffixTreeNode  = self._createRoot() # Tree root node (start = end = -1)

    # Algorithm components
    self._aNode:                  SuffixTreeNode = self.root  # Active node (where traversal starts for an extension)
    self._aEdge:                  int = -1                    # Active edge (which character is next during traversal)
    self._aLength:                int = 0                     # Active length (how far we need to walk down during traversal)
    self._remaining_suffix_count: int = 0                     # Remaining suffix count (how many suffixes need to be added)

    # Printing components (do not effect functionality but help print state)
    self._phase: int = -1 # Current phase

    self._createSuffixTree()

  @property
  def size(self: _SuffixTree) -> int:
    '''Number of nodes used by the suffix tree. Read-only'''
    return self._count

  @property
  def _aEdgeChar(self: _SuffixTree) -> str:
    '''Get character at active edge. Read-only'''
    return self._string[self._aEdge]

  def charAt(self: _SuffixTree, i: int) -> str:
    '''Get active character'''
    return self._string[i]

  def getSubstring(self: _SuffixTree, i: int, j: int) -> str:
    '''Get a substring of the input string based on start and stop indicies (inclusive)'''
    # Check if root since range(-1, 0) results in [-1] which will be an end of word terminal which is not technically correct
    if i == -1 and j == -1:
      return ''
    # Splice the part of the string we want
    return  self._string[i:j+1]

  def getSubstringFromNode(self: _SuffixTree, node: SuffixTreeNode) -> str:
    '''Get a substring from a suffix tree node'''
    return self.getSubstring(node.start, node.end)

  def _debugPrintExtension(self: _SuffixTree, n: int) -> None:
    '''Print details about the current extension'''
    _debugPrint(f' == Extension {n}: \'{self._string[n-1:self._phase+1]}\' ({self._remaining_suffix_count} left after Rule 1) ==')

  def _debugPrintRule1Changes(self: _SuffixTree, node: SuffixTreeNode, i: int) -> int:
    '''Print all Rule 1 extensions for debug logging. i is the number of extensions. Returns number of next extension for printing'''
    global SYMBOLS
    # This only does anything when debug is enabled. Shortcut return if DEBUG is not enabled
    if not DEBUG:
      return 0

    # If node is empty, return
    if node == None:
      return i

    # If node is a leaf, it is updated to reflect the new lowest point
    if node.isLeaf():
      self._debugPrintExtension(i)
      _debugPrint('Rule 1')
      return i + 1

    # Go through each child and print any Rule 1 changes
    for c in SYMBOLS:
      child = node.children[c]
      i = self._debugPrintRule1Changes(child, i)

    # Return current extension number
    return i

  def _createSuffixTree(self: _SuffixTree, pause: bool = False) -> None:
    '''Create the suffix tree'''
    global DEBUG
    # perform |S| extensions
    for i in range(self._size):
      # For each extension, the considered suffixes increase by 1
      self._extendSuffixTree(i)

      if (DEBUG):
        _debugPrint(f' ==== End of Phase {self._phase+1} State ====')
        _debugPrint(f'Active Node:   {self._aNode}')
        _debugPrint(f'Active Edge:   \'{self._aEdgeChar}\' / {self._aEdge}')
        _debugPrint(f'Active Length: {self._aLength}')
        _debugPrint(f'Suffixes Left: {self._remaining_suffix_count}')
        self.printSuffixTree(self.root)

      if (pause):
        if (input('Enter \'q\' to stop: ').lower() == 'q'):
          break

    _debugPrint(f' ===== Assigning Suffix Indicies =====')
    self._setSuffixIndexes(self.root, 0)

  def _extendSuffixTree(self: _SuffixTree, pos: int) -> None:
    '''Perform the ith extension phase to the suffix tree'''

    # Extension Rule 1: Add new character to existing leaf node
      # Update final position on leaf node
    # Extension Rule 2: Create new Leaf node (and possibly internal node if label lands between edges)
      # Create new leaf node and update parent's child array
      # Create new internal node if necessary
      # When unique terminals are added, they will be different for all leaves and all nodes will use Rule 2 to split. This allows future words to reuse the non-terminal branches for their computation.
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

    _debugPrint(f'========== Phase {pos+1} \'{self._string[pos]}\'  =========')
    _debugPrint(f'Adding suffixes: {[self._string[pos-i:pos+1] for i in range(pos, -1, -1)]}')

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
      if self._aLength == 0:
        #! APCFALZ (_aLength = 0)
        _debugPrint('APCFALZ')
        self._aEdge = pos

      # _aEdge transition from _aNode does not exist
      if self._aNode.children[self._aEdgeChar] == None:
        #! RULE 2 (new leaf is created, not requiring another node be split)
        _debugPrint('Rule 2 - No split')
        self._aNode.children[self._aEdgeChar] = self._createNode(True, pos)

        # If internal node was made before, update suffix link to active node
        if last_new_node != None:
          last_new_node.suffixLink = self._aNode
          last_new_node = None

      # _aEdge transition from _aNode exists
      else:
        # Get next node from active node taking active edge transition
        next_node = self._aNode.children[self._aEdgeChar]
        # See if _aLength brings us to or past the next node
        #! TRICK 1
        if self._walkDownTree(next_node):
          # Start extension from new activePoint and restart this iteration
          continue

        if self._string[next_node.start + self._aLength] == self._string[pos]:
          #! Rule 3 (current character being processed is on edge)
          _debugPrint('Rule 3')
          # Update internal node suffix link
          if last_new_node != None and self._aNode != self.root:
            last_new_node.suffixLink = self._aNode
            last_new_node = None
          #! APCFER3
          _debugPrint('APCFER3')
          self._aLength += 1
          #! TRICK 2
          break

        #! Rule 2 (new leaf node requiring splitting of an internal node)
        _debugPrint('Rule 2 - Split')

        # We have fallen off the tree and must create a new internal node to contain the new node
        split_end = next_node.start + self._aLength - 1 # new end position for split

        split_node = self._createNode(False, next_node.start, split_end) # new internal node
        self._aNode.children[self._aEdgeChar] = split_node # update active node child to point to new node

        split_node.children[self._string[pos]] = self._createNode(True, pos) # new leaf out from split node

        next_node.start += self._aLength # push updated node's start past the new node
        # split_node.children[self._aEdgeChar] = next_node # update child of split node with edge of next_node's first char
        split_node.children[self.charAt(next_node.start)] = next_node # update child of split node with edge of next_node's first char

        # Update previous internal node if needed
        if last_new_node != None:
          last_new_node.suffixLink = split_node

        # New internal node is missing its suffix link (currently pointing to root)
        # We need to update the suffix link to any new internal internal nodes created
        last_new_node = split_node

      # A suffix got added to the tree, decrement number of suffixes to be added
      self._remaining_suffix_count -= 1
      if self._aNode == self.root and self._aLength > 0:
        #! APCFER2C1
        _debugPrint('APCFER2C1')
        self._aLength -= 1
        self._aEdge = pos - self._remaining_suffix_count + 1
      elif self._aNode != self.root:
        #!APCFER2C2
        _debugPrint('APCFER2C2')
        self._aNode = self._aNode.suffixLink
        assert(self._aNode != None)

  def _walkDownTree(self: _SuffixTree, node: SuffixTreeNode) -> bool:
    '''Traverse down the active node'''
    # Walk down node depending on activePoint
    if self._aLength >= node.edgeLength:
      #! APCFWD
      _debugPrint('APCFWD')
      # Update all active components
      self._aEdge += node.edgeLength # next character
      self._aLength -= node.edgeLength
      self._aNode = node
      assert(self._aNode != None)
      return True
    return False

  def _nextID(self: _SuffixTree) -> int:
    self._count += 1
    return self._count-1

  def _createRoot(self: _SuffixTree) -> SuffixTreeNode:
    '''Create and return a new root node'''
    node = SuffixTreeNode(False, -1, -1, self._nextID())
    node.suffixLink = node
    node.suffixIndex = -1
    return node

  def _createNode(self: _SuffixTree, leaf: bool, start: int, end: int | None = None) -> SuffixTreeNode:
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

  def _setSuffixIndexes(self: _SuffixTree | None, node: SuffixTreeNode, labelHeight: int) -> None:
    '''Sets the suffix index for each leaf node in the tree. Internal nodes keep their default index. Done using DFS'''
    global SYMBOLS
    if node == None:
      return

    if node != self.root:
      _debugPrint(self.getSubstringFromNode(node))

    leaf = True
    for c in SYMBOLS:
      child = node.children[c]
      # Check for any children
      if child != None:
        if leaf and node.start != -1:
          _debugPrint(f' [{node.suffixIndex}]')

        # A child exists, so update that this node is not a leaf and recurse on that child
        leaf = False
        self._setSuffixIndexes(child, labelHeight + child.edgeLength)

    if leaf:
      # This node has no children, so update its suffix index
      node.suffixIndex = self._size - labelHeight
      _debugPrint(f' [{node.suffixIndex}]')

  def _getSuffixArray(self: _SuffixTree, node: SuffixTreeNode | None, lst: list[str] | None = None) -> list[str]:
    '''Recursive function to build suffix array in lst'''
    global SYMBOLS
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
    for c in SYMBOLS:
      child = node.children[c]
      lst = self._getSuffixArray(child, lst)

    return lst

  def _tidyTree(self: _SuffixTree, node: SuffixTreeNode) -> None:
    '''Updates all child leaf nodes under the input node to truncate the end label position at the first terminal'''
    global TERMINAL
    if node == None:
      return

    if not node.isLeaf():
      for c, child in node.children.items():
        self._tidyTree(child)

    else:
      front_word = self.getSubstringFromNode(node)
      for terminal in TERMINAL:
        front_word = front_word.split(terminal)[0] # Remove all characters after the first terminal
      node.end = node.start + len(front_word)

  def printSuffixTree(self: SuffixTree, node: SuffixTreeNode | None, indent: int = 0) -> None:
    '''Print the suffix tree as a simplified tree. Done using DFS'''
    global SYMBOLS
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

    for c in SYMBOLS:
      child = node.children[c]
      self.printSuffixTree(child, indent + 1)


class SuffixTree:
  '''Suffix Tree View/Controller Object'''
  def __init__(self: SuffixTree, strings: list[str]) -> SuffixTree:
    global TERMINAL
    if (len(strings) > len(TERMINAL)):
      raise Exception(f'Too many words given, maximum is {len(TERMINAL)}')
    for i, string in enumerate(strings):
      if not isValidWord(string):
        raise Exception(f'Input string \'{string}\' has invalid characters')
      if string[-1] not in TERMINAL:
        string += TERMINAL[i]
        _debugPrint(f'Adding terminal, new string is \'{string.replace(TERMINAL[i], f"${i}")}\'')
        strings[i] = string

    # Store modified input
    self._string: list[str] = strings

    # Create suffix tree. Assigns self.root
    self._tree: _SuffixTree = _SuffixTree(self.rawstring)
    self._tree._tidyTree(self.root) # truncate symbols in nodes

  @property
  def rawstring(self: SuffixTree) -> str:
    '''Raw string input to the suffix tree. Uses terminals. Read-only'''
    return ''.join(self._string)

  def _tidy(self: SuffixTree, s: str) -> str:
    '''Tidies the input string to make it suitable for printing by replacing terminals'''
    for i in range(len(TERMINAL)):
      s = s.replace(TERMINAL[i], f'${i}')
    return s

  @property
  def strings(self: SuffixTree) -> str:
    '''Return all input words. Read-only'''
    return tuple(self._tidy(w) for w in self._string)

  @property
  def string(self: SuffixTree, i: int) -> str:
    '''Return a specific input word. Read-only'''
    if not isinstance(i, int):
        raise Exception(f'Expected int, got {type(i)}')
    return self.strings[i]

  @property
  def length(self: SuffixTree) -> str:
    '''Number of input characters. Ready-only'''
    words = self.strings
    return len(''.join(words)) - len(words) # exclude 2nd character from tidied terminals

  @property
  def root(self: SuffixTree) -> SuffixTreeNode:
    '''Suffix tree root. Read-only'''
    return self._tree.root

  @property
  def size(self: SuffixTree) -> int:
    '''Number of suffix tree nodes. Read-only'''
    return self._tree.size

  def __repr__(self: SuffixTree) -> str:
    return stringSuffixTree(self.rawstring, self)

  def getSubstring(self: SuffixTree, i: int, j: int) -> str:
    '''Get a substring of the input string based on start and stop indicies (inclusive). Replaces all end-of-word terminals with $'''
    global TERMINAL
    string = self._tree.getSubstring(i, j)
    # Replace all terminals
    for i in range(len(TERMINAL)):
      string = string.replace(TERMINAL[i], f'${i}')
    return string

  def getSubstringFromNode(self: SuffixTree, node: SuffixTreeNode) -> str:
    '''Get a substring of the input string based on start and stop indicies (inclusive). Replaces all end-of-word terminals with $'''
    return self.getSubstring(node.start, node.end)

  def _getFirstWordComponent(self: SuffixTree, pos: int) -> str:
      '''Return word starting from pos up to the first terminal. Used to prevent string suffixes from exposing concatenated nature of multiple word support'''
      global TERMINAL
      full: str = self.rawstring[pos:]
      for i, c in enumerate(full):
          if c in TERMINAL: # check if each character is a terminal and cut short when one is found
              return self.getSubstring(pos, pos+i)
      return full

  def _printSuffixTree(self: SuffixTree, node: SuffixTreeNode | None, indent: int = 0) -> None:
    '''Print the suffix tree as a simplified tree. Done using DFS'''
    global SYMBOLS
    if node == None:
      return

    print('\t' * indent + f'\'{self.getSubstringFromNode(node)}\', {node} -> ', end='')
    link: SuffixTreeNode = node.suffixLink
    if link == self.root:
      print(f'ROOT') # shorthand for root
    elif link != None:
      print(f'\'{self.getSubstringFromNode(link)}\', {link}')
    else:
      print(f'None')

    for c in SYMBOLS:
      child = node.children[c]
      self._printSuffixTree(child, indent + 1)

  def printSuffixTree(self: SuffixTree) -> None:
      self._printSuffixTree(self.root, 0)

  def getSuffixArray(self: SuffixTree) -> list[int]:
    '''Returns the suffix array for the suffix tree'''
    return self._tree._getSuffixArray(self.root)#[1:] # skip first element

  def getStringSuffixArray(self: SuffixTree) -> list[str]:
    '''Returns the suffixes that make up the suffix array'''
    return [self._getFirstWordComponent(pos) for pos in self.getSuffixArray()]

  def getInverseSuffixArray(self: SuffixTree) -> list[int]:
    '''Returns the suffix array for the suffix tree'''
    sa = self.getSuffixArray()
    isa: list[int] = [0] * len(sa)
    for ind, pos in enumerate(sa):
      isa[pos] = ind
    return isa

  def getLCPArray(self: SuffixTree) -> list[int]:
    '''Returns the LCP array. Uses Kasai's algorithm'''
    sa = self.getSuffixArray()
    isa = self.getInverseSuffixArray()
    lcp: list[int] = [0] * len(sa)

    l = 0
    for i in range(len(lcp)):
      k = isa[i]
      j = sa[k-1] # j = phi(i)
      while self.rawstring[i+l] == self.rawstring[j+l]:
        l += 1
      lcp[k] = l
      if l > 0:
        l -= 1
    return lcp


def handle_inputs():
  '''Creates and then accepts input arguments from the command line'''
  parser = argparse.ArgumentParser(
    prog = __file__,
    description = 'Application to parse input strings into a generalized syntax tree.',
  )

  # Options
  parser.add_argument(
    '-a',
    default = stringlib.ascii_lowercase,
    dest = 'alphabet',
    help = 'set the input symbol alphabet (default: %(default)s)'
  )
  parser.add_argument(
    '-t',
    default = stringlib.ascii_uppercase,
    dest = 'terminal',
    help = 'set the terminal symbol alphabet. Can be string of symbols or number of terminal symbols (default: %(default)s)'
  )
  parser.add_argument(
    '-d',
    default = False,
    action = "store_true",
    dest = 'displaystring',
    help = 'print the string as part of the output (default: %(default)s)'
  )
  # Outputs
  out_grp = parser.add_mutually_exclusive_group()
  out_grp.add_argument(
    '--walkthrough',
    default = False,
    action = "store_true",
    dest = 'walkthrough',
    help = 'show algorithm steps and return. cannot be used with -o'
  )
  out_grp.add_argument(
    '-o',
    default = 'tree',
    choices = ['tree', 'sa', 'lcp', 'sfx'],
    dest = 'output_type',
    help = 'type of output. cannot be used with --walkthrough (default: %(default)s)'
  )
  # Inputs
  in_grp = parser.add_mutually_exclusive_group(required = True)
  in_grp.add_argument(
    '-p',
    default = 'none',
    choices = ['none', 'abac', 'abab', 'abca'],
    dest = 'preset',
    type = str,
    help = 'set a preset string as input (default: %(default)s)'
  )
  in_grp.add_argument(
    '-i',
    dest = 'input',
    action="store_true",
    help = 'take input strings from stdin'
  )
  in_grp.add_argument(
    '-w',
    nargs = '+',
    dest = 'word',
    help = 'take input as a sequence of words'
  )

  return parser.parse_args()


if __name__ == '__main__':
  def inlineSequencePrint(seq: list | tuple) -> None:
    print(f'{seq[0]}', end = '')
    for elem in seq[1:]:
      print(f' {elem}', end = '')
    print(f'')

  args = handle_inputs()

  DEBUG = args.walkthrough

  if args.alphabet:
    ALPHABET = str(args.alphabet)

  if args.terminal:
    if args.  terminal.isdigit():
      if int(args.terminal) > len(stringlib.ascii_uppercase):
        raise Exception(f'maximum terminals is {len(stringlib.ascii_uppercase)}')
      TERMINAL = str(stringlib.ascii_uppercase[:int(args.terminal)])
    else:
      TERMINAL = args.terminal

  # Validate settings
  assert not set(TERMINAL).intersection(set(ALPHABET)), f'There must be no overlap between alphabet and terminal characters'
  SYMBOLS = TERMINAL + ALPHABET

  # Parse input string
  if args.preset == 'none':
    if args.input == True:
      string = input('input string> ').split(' ')
    else:
      string = args.word
  else:
    if args.preset == 'abac':
      string = ['abacababacabacaba']
    elif args.preset == 'abab':
      string = ['abaabaab', 'abbaabbab']
    elif args.preset == 'abca':
      string = ['abcabxabcd']

  if DEBUG:
    print(f'Alphabet: {ALPHABET}')

  tree = SuffixTree(string)

  if args.displaystring:
    print('input: ', end='')
    inlineSequencePrint(tree.strings)

  if DEBUG:
    print(f"# Nodes = {tree.size}")
    print(stringSuffixTree(tree.rawstring, tree))
    exit()

  else:
    if args.output_type == 'tree':
      print(stringSuffixTree(tree.rawstring, tree))
      #tree.printSuffixTree()
    elif args.output_type in ('sa', 'lcp', 'sfx'):
      if args.output_type == 'sa':
        lst = tree.getSuffixArray()
      elif args.output_type == 'lcp':
        lst = tree.getLCPArray()
      elif args.output_type == 'sfx': # get suffix array as strings
        lst = tree.getStringSuffixArray()
      else:
        raise Exception(f'Unknown output array, {args.output_type}.')

      inlineSequencePrint(lst)
