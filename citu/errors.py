"""Diagnostics shared by every phase of the Citu compiler."""


class Diagnostic:
    """One compiler message tied to a source position."""

    def __init__(self, severity, phase, line, col, message, lexeme=None):
        self.severity = severity        # "error" | "warning"
        self.phase = phase              # "lexical" | "syntax" | "semantic"
        self.line = line
        self.col = col
        self.message = message
        self.lexeme = lexeme

    def __str__(self):
        where = "%d:%d" % (self.line, self.col)
        tail = "" if self.lexeme is None else "  (near '%s')" % self.lexeme
        return "%-8s %-8s %-7s %s%s" % (
            self.severity, self.phase, where, self.message, tail)

    def to_dict(self):
        return {
            "severity": self.severity,
            "phase": self.phase,
            "line": self.line,
            "col": self.col,
            "message": self.message,
            "lexeme": self.lexeme,
        }


class DiagnosticBag:
    """Collects diagnostics so a phase can report many problems, not just one."""

    def __init__(self):
        self.items = []

    def error(self, phase, line, col, message, lexeme=None):
        self.items.append(Diagnostic("error", phase, line, col, message, lexeme))

    def warning(self, phase, line, col, message, lexeme=None):
        self.items.append(Diagnostic("warning", phase, line, col, message, lexeme))

    @property
    def errors(self):
        return [d for d in self.items if d.severity == "error"]

    @property
    def warnings(self):
        return [d for d in self.items if d.severity == "warning"]

    def has_errors(self):
        return any(d.severity == "error" for d in self.items)

    def render(self):
        if not self.items:
            return "no diagnostics\n"
        lines = []
        for d in sorted(self.items, key=lambda d: (d.line, d.col)):
            lines.append(str(d))
        return "\n".join(lines) + "\n"


class CituFatal(Exception):
    """Raised when a phase cannot continue at all."""
