"""tests for the b+Tree implementation"""

from seriousdb.b_plus_tree import BPlusTree, _InternalNode, _LeafNode, _Node


def assertTreeStructure(tree: BPlusTree) -> None:
    root = tree._root

    if root is None:
        return
    # okay here i will just make it a really long for loop so it cannot run infenetly if there is an error in the tree code
    stack = [root]
    while len(stack) > 0:
        node: _Node = stack.pop()

        assert len(node._keys) <= tree._maxKeys

        if node is not tree._root:
            assert node._parent is not None

        if isinstance(node, _LeafNode):
            assert len(node._keys) == len(node._values)

        if isinstance(node, _InternalNode):
            assert len(node._children) == len(node._keys) + 1
            stack.extend(node._children)


def test_put_first_key():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)

    result = tree.put(1, b"2")

    assert result is True


def test_put_same_key():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)

    tree.put(1, b"2")
    result: bool = tree.put(1, b"2")

    assert result is False


def test_force_split():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)
    tree.put(1, b"AA")
    tree.put(2, b"AA")
    tree.put(3, b"AA")
    tree.put(4, b"AA")

    assertTreeStructure(tree)
    assert isinstance(tree._root, _InternalNode)


def test_stress_put():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)
    for i in range(0, 100000, 1):
        tree.put(i, b"bbb")

    assertTreeStructure(tree)


def test_get_success():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)

    tree.put(1, b"AA")
    value = tree.get(1)

    assert value == b"AA"


def test_get_empyTree():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)
    # retrive
    value = tree.get(1)
    assert value == None


def test_get_KeyNotInTree():
    maxChildren: int = 3
    tree: BPlusTree = BPlusTree(maxChildren)

    tree.put(2, b"AA")
    tree.put(3, b"BB")

    value = tree.get(5)
    assert value == None
