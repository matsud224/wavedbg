from collections import defaultdict

import vcd.common
from PySide6.QtCore import QAbstractItemModel, Qt, QModelIndex, QAbstractListModel
from vcd.reader import tokenize, TokenKind


class VCDScope:
    def __init__(self, name, scope_type, parent):
        self.name = name
        self.scope_type = scope_type
        self.parent = parent
        self.children = []
        self.vars = []

    def full_path(self):
        return self.parent.full_path() + '.' + self.name if self.parent else self.name

    def __str__(self):
        return f'{self.full_path()} ({self.scope_type})'


class VCDVar:
    def __init__(self, var_type, size, id_code, reference, bit_index):
        self.var_type = var_type
        self.size = size
        self.id_code = id_code
        self.reference = reference
        self.bit_index = bit_index
        self.value_changes = []

    def __str__(self):
        return f'{self.reference} (type={self.var_type}, size={self.size}, id={self.id_code}, bit={self.bit_index}, value_changes={self.value_changes})'


class VCDScopeTreeModel(QAbstractItemModel):
    columns = ['Name']

    def __init__(self, root_scope, parent=None):
        super().__init__(parent)
        self._root_scope = root_scope

    def get_item(self, index=QModelIndex()):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self._root_scope

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() and parent.column() > 0:
            return 0
        parent_scope = self.get_item(parent)
        if not parent_scope:
            return 0
        return len(parent_scope.children)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=None):
        if not index.isValid():
            return None
        if role != Qt.DisplayRole:
            return None
        item = self.get_item(index)
        match index.column():
            case 0:
                return item.name
            case 1:
                return item.scope_type.name
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return self.columns[section]

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()
        parent_scope = self.get_item(parent)
        if not parent_scope:
            return QModelIndex()
        child_scope = parent_scope.children[row]
        if child_scope:
            return self.createIndex(row, column, child_scope)
        return QModelIndex()

    def parent(self, index=QModelIndex()):
        if not index.isValid():
            return QModelIndex()
        child_scope = self.get_item(index)
        if child_scope:
            parent_scope = child_scope.parent
        else:
            parent_scope = None
        if parent_scope == self._root_scope or not parent_scope:
            return QModelIndex()
        return self.createIndex(parent_scope.children.index(child_scope), 0, parent_scope)


class VCDVarsListModel(QAbstractListModel):
    def __init__(self, vars, parent=None):
        super().__init__(parent)
        self._vars = vars

    def rowCount(self, parent=QModelIndex()):
        return len(self._vars)

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()
        return self.createIndex(row, column, self._vars[row])

    def data(self, index, role=None):
        if not index.isValid() or index.row() >= self.rowCount():
            return None
        if role != Qt.DisplayRole:
            return None
        var = self._vars[index.row()]
        return var.reference


class VCDLoader:
    @classmethod
    def load(cls, vcd_file):
        f = open(vcd_file, 'rb')

        metadata = {}
        value_changes_dict = defaultdict(list)
        vars = []
        root_scope = VCDScope('root', vcd.common.ScopeType.module, None)
        current_scope = root_scope
        current_time = 0

        for tok in tokenize(f):
            match tok.kind:
                case TokenKind.COMMENT:
                    metadata['comment'] = metadata.get('comment', '') + tok.comment.rstrip() + '\n'
                case TokenKind.DATE:
                    metadata['date'] = metadata.get('comment', '') + tok.date.rstrip() + '\n'
                case TokenKind.ENDDEFINITIONS:
                    pass
                case TokenKind.SCOPE:
                    new_scope = VCDScope(tok.scope.ident, tok.scope.type_, current_scope)
                    current_scope.children.append(new_scope)
                    current_scope = new_scope
                case TokenKind.TIMESCALE:
                    metadata['timescale'] = tok.timescale
                case TokenKind.UPSCOPE:
                    current_scope = current_scope.parent
                case TokenKind.VAR:
                    new_var = VCDVar(tok.var.type_, tok.var.size, tok.var.id_code, tok.var.reference, tok.var.bit_index)
                    current_scope.vars.append(new_var)
                    vars.append(new_var)
                case TokenKind.VERSION:
                    metadata['version'] = metadata.get('version', '') + tok.version.rstrip() + '\n'
                case TokenKind.DUMPALL:
                    pass
                case TokenKind.DUMPOFF:
                    pass
                case TokenKind.DUMPON:
                    pass
                case TokenKind.DUMPVARS:
                    pass
                case TokenKind.END:
                    pass
                case TokenKind.CHANGE_TIME:
                    current_time = tok.time_change
                case TokenKind.CHANGE_SCALAR:
                    value_changes_dict[tok.scalar_change.id_code] += (current_time, tok.scalar_change.value)
                case TokenKind.CHANGE_VECTOR:
                    value_changes_dict[tok.vector_change.id_code] += (current_time, tok.vector_change.value)
                case TokenKind.CHANGE_REAL:
                    value_changes_dict[tok.real_change.id_code] += (current_time, tok.real_change.value)
                case TokenKind.CHANGE_STRING:
                    value_changes_dict[tok.string_change.id_code] += (current_time, tok.string_change.value)

        for var in vars:
            var.value_changes = value_changes_dict[var.id_code]
        return metadata, VCDScopeTreeModel(root_scope)
