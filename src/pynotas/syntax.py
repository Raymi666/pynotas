"""Token colors without evaluating Python. Preserve source text and indentation."""
import io
import keyword
import tokenize

TEXT, STRING, NUMBER, KEYWORD, COMMENT = '#EFF5F8','#B5E7CA','#F8CF88','#CDBFF9','#ACBEC7'

def colored_lines(source):
    expanded=source.expandtabs(4)
    lines=expanded.splitlines()
    colors=[[TEXT]*len(line) for line in lines]
    try:
        for token in tokenize.generate_tokens(io.StringIO(expanded).readline):
            color=(STRING if token.type==tokenize.STRING else NUMBER if token.type==tokenize.NUMBER else
                   KEYWORD if token.type==tokenize.NAME and keyword.iskeyword(token.string) else
                   COMMENT if token.type==tokenize.COMMENT else TEXT)
            for row in range(token.start[0],token.end[0]+1):
                if 1<=row<=len(lines):
                    a=token.start[1] if row==token.start[0] else 0
                    b=token.end[1] if row==token.end[0] else len(lines[row-1])
                    a=min(a,len(lines[row-1]));b=min(b,len(lines[row-1]))
                    colors[row-1][a:b]=[color]*max(0,b-a)
    except (tokenize.TokenError,IndentationError):pass
    return zip(lines,colors)
