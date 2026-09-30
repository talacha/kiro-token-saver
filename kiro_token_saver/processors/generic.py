from . import Processor, collapse_repeats, head_tail


class GenericProcessor(Processor):
    """Fallback: strip blanks runs/trailing space, collapse repeats, keep head+tail."""

    name = "generic"

    def matches(self, argv):
        return True

    def process(self, text, cfg):
        lines = [ln.rstrip() for ln in text.splitlines()]
        squeezed, blank = [], False
        for ln in lines:
            if not ln:
                if blank:
                    continue
                blank = True
            else:
                blank = False
            squeezed.append(ln)
        lines = collapse_repeats(squeezed)
        return "\n".join(head_tail(lines, cfg.head_lines, cfg.tail_lines))
