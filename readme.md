# Generalized Suffix Tree
This project implements Ukkonen's algorithm, creating a generalized suffix tree from an input set of words. The algorithm appends each input word with a unique suffix character to allow the algorithm to parse multiple strings, preventing suffixes from being improperly merged between different words. The application's output is the generalized suffix tree structure which can then be queried for the suffix array and LCP array of the input. The application was built with extension in mind so each component can easily be updated and extended to modify the algorithm's behaviour or extend its functionality. The program is structured in a manner which separates the view and controller from the data model to help facilitate this. The application supports walkthroughs for the extensions and phases the algorithm takes.

This application an has an efficient implementation for Ukkonen's algorithm, suitable for retrieving string metadata arrays, such as suffix array and LCP array. This application can also be used as a teaching tool as it support writing all steps taken fron Ukkonen's algorithm.

## Introduction

### Background Information
Given any string, it can be broken down into a number of suffixes by repeatedly removing the first letter in that word. The suffixes produced by a word can provide a tremendous amount of information and are critical to many algorithms in string processing and are usable in a wide variety of fields. Additionally, even more information can be extracted from the suffixes when provided in sorted order, such as retrieval of the LCP array. Therefore, efficient calculation of this structure is a vital step in any string algorithm.

A trie is a structure which contains several nodes which are linked in a parent-child structure where any parent can have zero or more child nodes. The suffix tree starts from a root node which contains all other nodes within the tree. Therefore, each input string can insert all of its suffixes within the suffix tree. However, by assigning a node to a single letter results in tries which are extremely deep and space inefficient. Instead, the notion of a tree is created which collapses all nodes in a chain with one child into a single node (excluding the root). This allows the tree to model the desired structure while remaining efficient to traverse through. The cost of this optimization is more complex node insertion procedures which can split a node into two pieces in addition to appending a node to another node. A suffix tree is a tree which contains edges which correspond to a particular string's suffixes. This allows for a sturctured way to track suffixes of a particular string. A generalized suffix tree  is a suffix tree but instead of representing a single string's suffixes it provides suffixes for a set of input strings.

There are two types of nodes within the tree, internal and leaf nodes. An internal node represents a node with 1 or more children and a leaf node has no children. There is one special internal node which is the root node and it has no label and holds the rest of the tree. This node is always considered internal no matter how many children it has. Within Ukkonen's algorithm, the types of nodes represent different meanings. A leaf node provides a complete suffix when tracing the route from the leaf to the root whereas an internal node provides a way to structure the similarity in suffix structures. An interesting property within Ukkonen's algorithm is that once a node is a leaf node, it will always remain a leaf node. This is because the algorithm functions by extending each leaf node and then inserting missing suffixes into the suffix tree, inserting intermediate nodes as required. From how the lead and internal nodes are structured we can create a structure that can efficiently compute the suffix array in linear time.

Ukkonen's algorithm is a method of creating a generalized suffix tree by making an implicit suffix tree for each prefix of the input string, starting from the first character and moving towards the back. This means that there are a number of extension phases equal to the number of characters in the string and each phase contains a number of extensions equal to the number of suffixes the processed string at that point contains. The algorithm starts with an implicit suffix tree containing the first character of the string and then appends the next character onto the previous character's suffix tree. Thus, any suffix tree `Ti+1` is built on the suffix tree `Ti`. This construction is online, meaning that at any given point in the program, the application has the implicit suffix tree for the characters processed up to that point.

Each extension the algorithm does is by prepending a character for a suffix already in the tree (since we start with a suffix `x` and then for the next phase prepend `x` with another character and restart the phase) so when a new phase starts, the algorithm finds all suffixes previously entered into the tree and extends them. For each suffix extension, there are 3 rules:

1. If the path of a previous suffix is a leaf node, the next character extension will be added to the edge of that leaf node.
2. If the path of a previous suffix is an internal node and the next character extension will not remain within the existing tree, a new leaf node will be created to contain the new suffix. If this occurs in the middle of an existing internal node's edge, a new internal node will be created.
3. If the path of a previous suffix is an internal node and the next character extension will remain within the existing tree then nothing is done. Subsequent iterations of the algorithm will expand the suffix that was attempted here and eventually create a leaf node for it.

### Motivation
Ukkonen's algorithm is an extremely well known algorithm and has been well studied however, there are few easily usable implementations. The goal of this application is to create a version of the algorithm that is efficient, useful and easy to extend and understand. I also find software tools and algorithms facinating to create.

### Contribution
This implementation of Ukkonen's algorithm supports the inclusion of multiple words into the generalized suffix tree. This is achieved by using unqiue terminal characters for each word which prevents the suffixed from different words from merging together. Additionally, I added data structures to help maintain the integrity of the algorithm and prevent silent failures. These structures should be fast to use and prevent extra resource usage while still protecting the algorithm.

## Implementation
The implementation is split into several classes which build upon one another and implement a general functionality required by the application.

The class `_SuffixNodeReference` is a class which helps maintain a proper state of the algorithm. It ensures that any variable that is assigned to an instance of it is only assigned a `SuffixTreeNode` value or `None`. This prevents the user or algorithm from assigning an invalid value. This class functions using Python's `property` interface to ensure correctness.

The class `_SuffixNodeDict` is similar to `_SuffixNodeReference` in that it maintains the children of a `SuffixTreeNode` instance. It also prevents assignents of values that are of inproper type, like `_SuffixNodeReference`. This class functions by disallowing improper assignments and mantaining a minimal size for the internal hash table.

`SuffixTreeNode` is the class used for each node within the suffix tree. This class represents both internal and leaf nodes. To ensure that each leaf node always points to the last index of the string (before being tidied), a unique value of `None` is stored for the `_end` property. Then when the application queries the `end` property, it checks if the value of `_end` is `None` and if so, it returns the global value which represents the end of the string. This allows for each node to automatically update itself as the string is processed without any word from the application. Each node also keeps track of whether it is a leaf, a reference to its suffix link, the string start label index and the order of itself in the suffix array. Equality is required to correctly compute Ukkonen's algorithm so this relation is defined for this class and checks if the start, end and suffix links are identical.

The `_SuffixTree` class is the main data model of the application. This class encapsulates Ukkonen's algorithm, creating an optimized representation for entered strings. This class implements the algorithm as described by the [background information](#background-information). This class encompasses all required state variables of the algorithm, including the active edge, active node, active length, remaining suffix count and input string. The algorithm works by iteratively adding each suffix, starting from just the first character and then extending the suffixes from the front of the string, just as described by Ukkonen's algorithm. This class contains extensive debug printing capabilities and implements well known optimizations and tricks employed by other Ukkonen's algorithm implementations. Additionally, the abilitiy to clean the tree is also available which sets each leaf node's `end` field to be the first terminal character seen in the string. This hides the unique terminal characters and concatenation of the input words from the user and makes the algorithm easier to use and understand.

Lastly, the `SuffixTree` class is the view and controller for the application. This class wraps the `_SuffixTree` class manages the data contained within. It also provides ways to query and display the data for the user. This class is the main class meant to be exported and used by the user. This class supports suffix array and lowest common prefix array queries though it can easily be extended to support more. It also contains metadata for the input strings.

This implementation is a static representation of the input strings, so it does not support modification of the structure after it has been created. The primary `SuffixTree` class implements the generalized suffix tree creation algorithm in linear time, the same as Ukkonen's algorithm.

## Program

### Prerequisites
This application was written in pure Python 3 with no non-standard libraries. This means it can run on any system with a full Python 3 standard library. Additionally, because this is written in Python, there are no makefiles or other steps to create an executable program.

### Inputs
The application takes three inputs: a string representing each character in the alphabet, a string representing each terminal character or a number of terminal characters and a list of input strings.

The alphabet is the set of allowable characters in input words. If a input character is found to not be in The alphabet, an error will be raised notifying the user and halting the application. The alphabet is expected to be a string of non-repeating characters. By default, the application assumes the alphabet is all lowercase ASCII characters unless given as an input using the `-a` flag. Similarly, the terminal characters is a string of unique characters with respect to other characters within the terminal character string and the characters within the alphabet string. This input is used to append each input string with a unique character. This prevents each string from being merged within the tree. Note that because the terminals are defined as unique characters, the number of input words to the application are limited by the number of terminal characters given. The number of terminal characters is given by the `-t` flag.

The default alphabet is all lowercase letters and terminals is all uppercase letters. This means all input words must be lowercase and there are a maximum of 26 words per suffix tree.

The most inportant input is the words which will be entered into the suffix tree. The characters within each string must be a part of the defined alphabet. If a word contains an invalid word there will be an error raised. To handle multiple words, a unique terminal is appended to each word that isn't part of the alphabet. These terminals is what allows the algorithm to handle multiple input words because the terminals prevent suffixes of the different words from getting merged. The number of input words are limited by the number of unique terminals available.

The input words can be provided in 4 ways using the `-p`, `-i`, `-f` and `-w` flags. The `-p` flag will use a preset string set as input. There are currently 2 options, `abac` and `abab`. If `abac` is used, the input strings is `abacababacabacaba` and if `abab` is used, the input strings are `abaabaab` and `abbaabbab`. The `-i` flag will take input from standard input and use those words as input. When accepting input from standart input, the input words will be split at spaces. The `-w` flag accepts an amount of words within the given alphabet up to the number of terminal characters and uses those words as input. The `-f` flag accepts a file path as input and will use that file as the input string. The file contents will be read and any spaces, tabs or newlines will be treated as word separators and therefore will be made into different words. So to ensure a word in a file is not broken up accidentally, ensure there are no spaces, newlines or tabs that break up the word. The last flag is `-w` which accepts an arbitrarily long sequence of words to use as input. Each word will be used as an input. Note that all the above flags are restricted in the number of words permitted by the number of terminal characters provided through the `-t` option.

### Outputs
There are 4 outputs the application can accept, a tree describing the generated generalized suffix tree, the suffix array for the input words, the lcp array or the strign suffixes sorted in suffix array order. The application can also take a `--walkthrough` flag which replaced the output and provides all steps taken in the computation of Ukkonen's algorithm for the given input.

The default output is the suffix tree text representation, so this output will be provided if no `-o` flag is passed to the application. The tree starts at the root and all its children and those subchildren are printed. Each printed node either has the leaf format of `label [id] (index)` or internal format of `label [id] -> node`. `label` is the characters on the edge leading to the node. `id` is the node's ID and is useful for differentiating nodes that share the same `label`. `index` is the position in the input string the leaf terminates at and is useful for finding the suffix this node represents. This is the value of the node in the suffix array. Internal nodes (those which have children) are missing the `index` value because they dont correspond to completed suffixes but they include the `node` value which represents the node which their suffix link connects to.

If the `-o` flag is given the value `sa`, then the suffix array will be outputted. The suffix array is a printed series of numbers which is the suffix array for the input set of strings. If a value of `sfx` is given to `-o`, instead of numbers, the string suffixes of the suffix array will be given instead. The last value `-o` can take is `lcp` which will print the LCP array for the input string.

If this file is imported into another Python script as a module, the `SuffixTree` class is the primary output which provides a wrapper for interacting with the suffix tree. The tree structure is maintained in the tree after creation, so additional operations using its data can easily extend the code.

### Options
The option `-d` will display the input strings as part of the output, allowing the user to see exactly what was input into the program and verify the input is what they intended.

The option `-h` will display a help message and exit the program. This help printout provides an explanation of all available options and how to use them.

### Usage
This application includes a shebang at the top of the source file allowing the command  `env` at `/usr/bin/env` to use a `python` environment to execute this application. This expects a Python 3 environment and requires execution permissions for the `gst.py` file. If `python` is not a Python 3 installation or the Python environment is unavailable, the application can instead be run with the `python3` command. Below show both ways of calling the application.

```bash
./gst.py -p abac        # use shebang
python gst.py -p abac   # use explicit python command
```

To use the different application inputs, simply include the desired flag in the command call. Below shows usage of the `-p`, `-w` and `-i` flags. Note that the `-i` command will require input from standard input after execution and therefore does not take input from the command line.

```bash
./gst.py -p abac                # use preset
./gst.py -w abaabacaba bacaaba  # use explicit words
./gst.py -i                     # use standard input
```

Application outputs `--walkthrough` and `-o` are mutually exclusive and `-o` can take inputs `tree`, `sa`, `lcp`, `sfx`. By default, `--walkthrough` is disabled and `-o` is set to `tree`. These flags are included alongside the input flags and are shown below.

```bash
./gst.py -p abac                # get default output (tree)
./gst.py -p abac --walkthrough  # get algorithm steps printout
./gst.py -p abac -o tree        # get tree output
./gst.py -p abac -o sa          # get suffix array output
./gst.py -p abac -o sfx         # get string suffix array output
./gst.py -p abac -o lcp         # get lcp array output
```

The optional flags `-a`, `-t`, and `-d` can be combined with all other flags to modify behaviour of the application. Below are examples of their use.

```bash
./gst.py -p abac -a abac  # define alphabet of a, b and c
./gst.py -p abac -t ABC   # define 3 terminals (max 3 input words and A, B, and C are excluded from the alphabet)
./gst.py -p abac -d       # display input words to algorithm
```

When used as a library, the `SuffixTree` class is the primary class to interact with the contents of this application. This class must be supplied with a list of input strings. Below is an example of importing the class, initializing and retrieving data.

```python
import SuffixTree, stringSuffixTree from gst
st = SuffixTree(['abcabxabcd'])
print(st)
sa = st.getSuffixArray()
lcp = st.getLCPArray()
```

Below is a list of relevant class methods and properties for `SuffixTree`. `SuffixTree` supports being turned into a string with the `str()` function:
- `words`: Return all input words.
- `word(i)`: Return a specific input word from index.
- `length`: Number of input characters.
- `root`: Return the root node of the suffix tree.
- `printSuffixTree`: Print a detailed representation of the suffix tree. Useful for seeing more details about the suffix tree.
- `getSuffixArray`: Return the suffix array for the input strings.
- `getStringSuffixArray`: Return the suffixes sorted in suffix array order.
- `getLCPArray`: Return the LCP array from the input strings.

### Limitations
This application does have some usage limitations which must be followed for proper execution. First and most imporantly, the suffix tree representation is assumed to be static from the algorithm. Once a suffix tree is created by a `SuffixTree` object, it will not allow modification to the representation. Secondly, only one tree can be processed at a time due to the global LEAFEND variable. To allow all leaves to grow and keep code simple, I needed to implement a global variale that could track the end of the string for all leaf nodes during processing. During `_SuffixTree._tidyTree` the reference to this global is removed, allowing more suffix trees to be created but two trees cannot be concurrently built due to sharing the global. This means that the `SuffixTree` class is not thread-safe. Lastly, due to terminals being represented as literal characters within the application, the number of words and characters of the alphabet are limited by the values within the `TERMINAL` global variable.

## Challenges
When developing this application, there were numerous challenges that were encountered.

The first challenge and the most prevalent was maintaining a valid tree throughout execution. When the application was under development, it was very difficult to ensure each component of the algorithm was acting how it was supposed to and there were numerous instances where the application would appear to be functional and then break once the input was changed. When trying to solve these sorts of errors, I noticed that the errors were usually a result of an invalid tree in some manner, like a issing suffix link, invalid character index or miscounting of the number of children a node has. These errors justified a more complex node representation with guards built in to prevent the tree from going into a bad state. This way if something goes wrong when modifying the program's behaviour, the application will provide feedback warning that the application is entering an error state.

A subproblem of the above challenge was how Python treats dicts and lists by reference but integers and strings by value. This resulted in numerous cases of aliasing between objects. The developed classes helped prevent this issue from occuring.

The second challenge was how to efficiently update all leaf nodes as the algorithm extended the suffixes it was considering. Ideally, it would be a property of the model but to prevent messy code and spaghetti references throughout the code to track a single value I instead decided on a single global variable. This allowed for clean access everywhere in the code however it does mean that only one suffix tree can be generated at a time. I did try to mitigate this issue with the method `_SuffixTree._tidyTree()` which sets each leaf node's `_end` property to the first terminal seen, preventing it from using the `None` value that translates to the end of the string.

Lastly, the algorithm's active point was a challenge to implement. Ukkonen's algorithm describes the active point like a single entity containing three values which provide easy traversal through the suffix tree. However, the algorithm only access and modifies the active point by one property at a time so instead of implementing another class to encapsulate this secret, I instead decided to make each component of the active point a property of the `_SuffixTree` class and update them separately. I believe this makes sense as the active point is a part of the algorithm encapsulated by the `_SuffixTree` class and there is no major benefit of abstracting away this class because it does not provide any unique functionality beyond storing values.

## Conclusion

### Improvements
The current implementation is versatile however there are improvements that can be made to improve the application even further. The first improvement would be to modify how the unique word terminals are tracked. Currently, there is a list of string characters distinct from the alphabet characters that are appended in order to each of the input words. The issue with this implementation is that the number of input words are limited by the number of terminal symbols set aside. Additionally, for each character assigned to a terminal, that is one less symbol that can be in the alphabet. There is no reason why terminals need to be unique symbols, instead they could all share a single symbol and then the `_SuffixTree` could in some way keep track of how many terminals have been seen and assign a way to keep them unique during proprocessing.

### Future Work
A major extension to this application would be to make the representation non-static. Currently, once the suffix tree is created, it cannot append any new words or modify its representation in any way however there are use cases where new input words may be provided and thus the user may want to insert them into the suffix tree. Additionally, the global variables within the file can be placed into some options class and then it can be stored in each `SuffixTree` class. This would allow each `SuffixTree` instance to track its own options and act independantly of eachother.
