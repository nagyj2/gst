# Generalized Suffix Tree
This project implements Ukkonen's algorithm, creating a generalized suffix tree from an input set of words. The algorithm appends each input word with a unique suffix character to allow the algorithm to parse multiple strings when they are actually just concatenated together. The file's output is the generalized suffix tree structure which can then be queried for the suffix array and LCP array. The application was built with extension in mind so each component can easily be updated and extended to modify the algorithm's behaviour or extend its functionality. The program is structured in a manner which separates the view and controller from the data model to help facilitate this. The application supports walkthroughs for the extensions and phases the algorithm takes.

## Introduction

### Background Information
Given any string, it can be broken down into a number of suffixes by repeatedly removing the first letter in that word. The suffixes produced by a word can provide a tremendous amount of information and are critical to many algorithms in string processing and are usable in a wide variety of fields. Additionally, even more information can be gotten from the suffixes when provided in sorted order, such as retrieval of the LCP array. Therefore, efficient calculation of this structure is a vital step in any algorithm.

A trie is a structure which contains several nodes which are linked in a parent-child structure where any parent can have zero or more child nodes. All parent nodes descend from some root node which contains the entire trie, thus a trie is a manner in which suffixes can be stored by establishing a node in the trie for each string in the suffix. However, by assigning a node to a single letter results in tries which are extremely deep and space inefficient. Instead, the notion of a tree is created which collapses all nodes in a chain with one child into a single node (excluding the root). This allows the tree to model the desired structure while remaining efficient to traverse through.

There are two types of nodes within the tree, internal and leaf nodes. An internal node represents a node with 1 or more children and a leaf node has no children. There is one special internal node which is the root node. This is from where the tree starts. This node is always considered internal no matter how many children it has. Within Ukkonen's algorithm, the types of nodes represent different meanings. A leaf node provides a complete suffix when tracing the route from the leaf to the root whereas an internal node provides a way to structure the similarity in suffix structures. From how the lead and internal nodes are structured we can create a structure that can efficiently compute the suffix array.

### Motivation
Ukkonen's algorithm is an extremely well known algorithm and has been well studied however, there are few easily usable implementations. The goal of this application is to create a version of the algorithm that is efficient, useful and easy to extend and understand. I also find software tools and algorithms facinating to create.

### Contribution
This implementation of Ukkonen's algorithm supports the inclusion of multiple words nto the generalized suffix tree. This is achieved by using unqiue terminal characters for each word which prevents the suffixed from different words from merging together. Additionally, I added two data structures to help maintain the integrity of the algorithm and prevent silent failures. These structures should be fast and prevent extra resource usage while still protecting the algorithm.

## Implementation
The implementation is split into several classes which build upon one another and implement a general functionality required by the application.

The class `_SuffixNodeReference` is a class which helps maintain a proper state of the algorithm. It ensures that any variable that is assigned to an instance of it is only assigned a `SuffixTreeNode` value or `None`. This prevents the user or algorithm from assigning an invalid value. This class functions using Python's `property` interface.

The class `_SuffixNodeDict` is similar to `_SuffixNodeReference` in that it maintains the children of a `SuffixTreeNode` instance. It also prevents assignents of values that are of inproper type, like `_SuffixNodeReference`.

`SuffixTreeNode` is the class used for each node within the suffix tree. This class represents both internal and leaf nodes. To ensure that each leaf node always points to the last index of the string (before being tidied), a unique value of `None` is stored for the `_end` property. Then when the application queries the `end` property, it checks if the value of `_end` is `None` and if so, it returns the global value which represents the end of the string. This allows for each node to automatically update itself as the string is processed without any word from the application. Each node also keeps track of whether it is a leaf, a reference to its suffix link, the string start label index and the order of itself in the suffix array.

The `_SuffixTree` class is the main data model of the application. This class encapsulates Ukkonen's algorithm, creating an optimized representation for whatever strings are entered. This class encompasses all required state variables of the algorithm, including the active edge, active node, active length, remaining suffix count and input string. The algorithm works by iteratively adding each suffix, starting from just the first character and then extending the suffixes from the front of the string, just as described by Ukkonen's algorithm. This class contains extensive debug printing capabilities and implements well known optimizations and tricks employed by other Ukkonen's algorithm implementations. Additionally, the abilitiy to clean the tree is also available which sets each leaf node's `end` field to be the first terminal character seen in the string. This hides the unique terminal characters and concatenation of the input words from the user and makes the algorithm easier to use and understand.

Lastly, the `SuffixTree` class is the view and controller for the application. This class wraps the `_SuffixTree` class and provides a way to initialize the `_SuffixTree` class and interact with the various outputs and properties of the generated suffix tree.

This implementation is a static representation, so it does not support modification of the structure after it has been created.

## Program

### Prerequisites
This application was written in pure Python 3 with no non-standard libraries. This means it can run on any system with a full Python 3 standard library. Additionally, because this is written in Python, there are no makefiles or other steps to create an executable program.

### Inputs
The inputs to this program is a list of strings. The characters within each string must be a part of the defined alphabet. If a word contains an invalid word there will be an error raised. To handle multiple words, a unique terminal is appended to each word that isn't part of the alphabet. These terminals is what allows the algorithm to handle multiple input words because the terminals prevent suffixes of the different words from getting merged. The number of input words are limited by the number of unique terminals available.

The default alphabet is all lowercase letters and terminals is all uppercase letters. This means all input words must be lowercase and there are a maximum of 26 words per suffix tree.

### Outputs
When the tree object is instantiated, the generalized suffix tree is created. This includes adding all words to the tree and truncating labels at the end to only contain characters until the first terminal. The user can then query the tree for the suffix array, inverse suffix array or the LCP array.

The tree structure is maintained in the tree after creation, so additional operations using its data can easily extend the code.

### Usage
A sample execution of the code would be:

```python
python gst.py atcgatcga atcca gaak
```

### Limitations
- One SuffixTree can be processed at a time thanks to global LEAFEND
- Only 26 words rn due to TERMINAL limit

### Challenges
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
