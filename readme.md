# Generalized Suffix Tree
This project implements Ukkonen's algorithm, creating a generalized suffix tree from an input set of words. The file's output is the generalized suffix tree structure which can then be queried for the suffix array and LCP array. The tree can also be printed out as text.

## Background

### Trees

#### Nodes

### Algorithm

## Application
The application does not allow additional words to the suffix tree once the tree has been created.

### Prerequisites
This application was written in pure Python 3 with no non-standard libraries. This should mean it can run on any system with a full Python 3 standard library. Additionally, because this is written in Python, there is no makefile or other steps to create an executable application.

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

## Project

### Motivation
- Could not find any implementations handling multiple words

### Contribution
- Data structures to maintain tree integrity and minimize space
- Implementation allowing for multiple words

### Challenges
- Maintaining a valid tree during execution
- How to handle Rule 1
- Python acts weird with dicts and lists as properties
- Implementation of the active point

## Conclusion

### Improvements
- Another way to track terminals that arent string symbols
- Adding new strings to the graph after creation

### Future Work
- More metadata arrays
