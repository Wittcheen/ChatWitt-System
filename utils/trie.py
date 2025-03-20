# (c) 2025 Christoffer Wittchen
# Released under the MIT License.

class _TrieNode:
    def __init__(self):
        """ Defines a Node for usage in a Trie """
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        """ Initialize the Trie with a root node. """
        self.root = _TrieNode()

    def __repr__(self):
        """ Recursively prints the structure of the Trie in a readable format.\n
        Indicates the end of words with `$` """
        def __recur(node: _TrieNode, indent: str):
            return "".join(indent + char + ("$" if child_node.is_end else "") + __recur(child_node, indent + "  ")
                for char, child_node in node.children.items())
        return __recur(self.root, "\n")

    def insert(self, word: str):
        """ Inserts a word into the Trie. """
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = _TrieNode()
            node = node.children[char]
        node.is_end = True

    def remove(self, word: str):
        """ Removes a word from the Trie. Does nothing if the word does not exist. """
        def __remove(node: _TrieNode, word: str, index: int) -> bool:
            if index == len(word):
                if not node.is_end:
                    return False # Word not found
                node.is_end = False
                return len(node.children) == 0 # True if node has no children
            char = word[index]
            if char not in node.children:
                return False # Word not found
            can_delete_child = __remove(node.children[char], word, index + 1)
            if can_delete_child:
                del node.children[char]
                return len(node.children) == 0 # True if node has no children
            return False
        __remove(self.root, word, 0)

    def clear(self):
        """ Clears the entire Trie, removing all words. """
        self.root = _TrieNode()

    def contains(self, word: str) -> bool:
        """ Checks if a word is in the Trie. """
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def search(self, prefix: str):
        """ Searches for words in the Trie that match the given prefix. """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self.__collect_words(node, prefix)

    def __collect_words(self, node: _TrieNode, prefix: str):
        """ Helper function to collect all words starting from a given node and prefix. """
        words = []
        if node.is_end:
            words.append(prefix)
        for char, child_node in node.children.items():
            words.extend(self.__collect_words(child_node, prefix + char))
        return words
