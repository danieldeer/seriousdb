"""b+tree implementation for datalookups in O(log n).

this module will hold the b+tree datastructure for loading and deleting data in and out of memory
!IMPORTANT this implementation is not Threadsafe
"""

from __future__ import annotations


class _Node:
    """internal class representing a node from the b+Tree."""

    _parent: _InternalNode | None
    _keys: list[int]

    def __init__(self) -> None:
        self._parent = None
        self._keys = []


class _LeafNode(_Node):
    """internal class representing a _leafnode from the b+Tree."""

    _values: list[bytes]
    _next_leaf: _LeafNode | None

    def __init__(self) -> None:
        super().__init__()
        self._values = []
        self._next_leaf = None


class _InternalNode(_Node):
    """internal class representing."""

    _children: list[_Node]

    def __init__(self) -> None:
        super().__init__()
        self._children = []


class BPlusTree:
    """a Btree like Datastructure to retrieve and put data in O(log n) time.

    the public functions will firstly be get() put() delete() range()

    !IMPORTANT: this structure is currently not threadsafe.

    Parameters
    ----------
    _maxChildren :int
        the tree takes in the maximum number of children a internal node should have.

    Attributes
    ----------
    _maxChildren : int
        The maximum number of children (mostly in literature visualized as m) an internal Node can point to
    _maxKeys: int
        The maximum number of Keys a _Node can hold derrived from the maximum number of children (m -1)
    _root : _Node or None
        the root Node of the tree the first will be a leafNode and after enough insertions mostly an internal Node

    Raises
    ------
    ValueError if the maxchildren parameter is below 3
    """

    _maxChildren: int = 0
    _maxKeys: int = 0
    _root: _LeafNode | _InternalNode | None
    _size: int = 0

    def __init__(self, maxChildren: int) -> None:
        if maxChildren < 3:
            raise ValueError("maxChildren must be at least 3")
        self._maxChildren = maxChildren
        self._maxKeys = self._maxChildren - 1
        self._root = None
        self._size = 0

    def put(self, key: int, value: bytes) -> bool:
        """Put an key value pair into the tree.

        if the tree is empty a leafNode is created at root and filled with the first key and value.
        if the tree alereay has some nodes the search starts. The next node from the children gets chosen via the comparator keys.
        If a leafnode has to many values or keys put splits the leafnote.

        Parameters
        ----------
            key : int
                the key to access the value.
            value : bytes
                bytes (Pages) to store.

        Returns
        -------
            is_new_key : bool
                ``True`` if `key` did not exist before, ``False`` if an existing
                value was replaced.
        """
        is_new_key = True
        self._size += 1
        if self._root is None:
            self._root = self._createLeaf(key, value)
            return is_new_key

        node: _LeafNode | _InternalNode | _Node = self._root
        while True:
            if isinstance(node, _LeafNode):
                if self._isKeyInLeaf(node, key):
                    key_index = node._keys.index(key)
                    node._values[key_index] = value
                    return False

                # NOTE: this find_position call only works because we check for duplicates in the if case before maby for later its more smart to make 2 helpers out of this
                insert_index: int = self._find_position(node._keys, key)

                node._keys.insert(insert_index, key)
                node._values.insert(insert_index, value)

                self._check_split(node)
                return True
            elif isinstance(node, _InternalNode):
                internalNode: _InternalNode = node
                nodeIndex = self._find_position(internalNode._keys, key)
                node = internalNode._children[nodeIndex]

    def get(self, key: int) -> bytes | None:
        """Return a value from the given key. if the key does not exist in the tree this function returns None.

        Parameters
        ----------
        key : int
            the key to access the value.

        Returns
        -------
        value : bytes | None
            returns bytes if the key is in the tree otherwise this function returns None
        """
        value: bytes | None = None
        if self._root is None:
            return value

        node: _InternalNode | _LeafNode | _Node = self._root
        while isinstance(node, _InternalNode):
            nodeIndex: int = self._find_position(node._keys, key)
            node = node._children[nodeIndex]

        # node should always be a _LeafNode this might be to defensive
        if isinstance(node, _LeafNode) and key in node._keys:
            keyIndex: int = node._keys.index(key)
            value = node._values[keyIndex]

        return value

    def size(self) -> int:
        """Return the current keyvaluePairs in the tree.

        Returns
        -------
        value : int
            returns the number of keyvalue pairs in the tree
        """
        return self._size

    def delete(self, key: int) -> bool:
        """Delete algorithm deletes key value pair."""
        return True

    """------ INTERNAL FUNCTIONS ------"""

    def _createLeaf(self, key: int, value) -> _LeafNode:
        node = _LeafNode()
        node._keys.append(key)
        key_index = node._keys.index(key)
        node._values.insert(key_index, value)
        return node

    def _createInternal(self, key, child1, child2) -> _InternalNode:
        internalNode: _InternalNode = _InternalNode()
        internalNode._keys.append(key)
        internalNode._children.append(child1)
        internalNode._children.append(child2)

        return internalNode

    def _isKeyInLeaf(self, node: _LeafNode, key: int) -> bool:
        return key in node._keys

    def _find_position(self, keys: list[int], key: int) -> int:
        insert_index: int = 0

        while insert_index < len(keys) and keys[insert_index] <= key:
            insert_index += 1

        return insert_index

    def _split_leaf(self, node: _LeafNode) -> None:
        newLeaf: _LeafNode = _LeafNode()
        keyLen: int = len(node._keys)
        splitIndex: int = keyLen // 2

        newLeaf._keys = node._keys[splitIndex:]
        newLeaf._values = node._values[splitIndex:]

        node._keys = node._keys[:splitIndex]
        node._values = node._values[:splitIndex]

        newLeaf._next_leaf = node._next_leaf
        node._next_leaf = newLeaf

        newSeperator: int = newLeaf._keys[0]

        if node._parent is None:
            # if the parent of an leafnote is None it is guaranteed that the leafnote lies at root.
            internalNode: _InternalNode = self._createInternal(
                newSeperator, node, newLeaf
            )

            newLeaf._parent = internalNode
            node._parent = internalNode
            self._root = internalNode
        else:
            parent: _InternalNode = node._parent

            child_index: int = parent._children.index(node)
            parent._children.insert(child_index + 1, newLeaf)
            parent._keys.insert(child_index, newSeperator)
            newLeaf._parent = parent

            self._check_split(parent)

    def _split_internal(self, node: _InternalNode) -> None:
        oldNode = node
        newNode = _InternalNode()

        keyLen: int = len(node._keys)
        splitIndex: int = keyLen // 2

        tempKey = oldNode._keys[splitIndex]
        newNode._keys = oldNode._keys[splitIndex + 1 :]
        oldNode._keys = oldNode._keys[:splitIndex]

        newNode._children = oldNode._children[splitIndex + 1 :]
        oldNode._children = oldNode._children[: splitIndex + 1]

        for child in newNode._children:
            child._parent = newNode

        if oldNode._parent is None:
            internalNode: _InternalNode = self._createInternal(
                tempKey, oldNode, newNode
            )

            newNode._parent = internalNode
            oldNode._parent = internalNode
            self._root = internalNode
        else:
            parent: _InternalNode = oldNode._parent

            child_index: int = parent._children.index(oldNode)
            parent._children.insert(child_index + 1, newNode)
            parent._keys.insert(child_index, tempKey)
            newNode._parent = parent

            self._check_split(parent)

    def _check_split(self, node: _Node | _InternalNode | _LeafNode) -> None:
        if len(node._keys) <= self._maxKeys:
            return

        if isinstance(node, _LeafNode):
            self._split_leaf(node)
        elif isinstance(node, _InternalNode):
            self._split_internal(node)
