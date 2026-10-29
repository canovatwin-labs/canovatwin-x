"""Public errors contain no SQL text, database paths or stored payloads."""


class StorageError(RuntimeError):
    code = "STORAGE_ERROR"


class StorageBusy(StorageError):
    code = "STORAGE_BUSY"


class NotFound(StorageError):
    code = "NOT_FOUND"


class Conflict(StorageError):
    code = "CONFLICT"


class InvalidTransition(StorageError):
    code = "INVALID_TRANSITION"


class UnsupportedSchema(StorageError):
    code = "UNSUPPORTED_SCHEMA"


class CorruptRecord(StorageError):
    code = "CORRUPT_RECORD"


class ReplayIncompatible(StorageError):
    code = "REPLAY_INCOMPATIBLE"
