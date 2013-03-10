'''
export to pdf or word
'''

import PyRTF, Image
from StringIO import StringIO
import os, re, urllib, datetime
from HTMLParser import HTMLParser
from xhtml2pdf.document import pisaDocument
from askbot.skins.loaders import get_template
from django.conf import settings

RE_LATEX = re.compile(r'(\${1,2})[^\$]+\1')
RE_STRIP = re.compile(r'<strip>(.+?)</strip>', re.S)
RE_CODE = re.compile(r'<code>(.+?)</code>', re.S)
RE_OL = re.compile(r'<ol>(.+?)</ol>', re.S)
RE_UL = re.compile(r'<ul>(.+?)</ul>', re.S)
RE_LI = re.compile(r'<li>(.+?)</li>', re.S)
RE_BLOCKQUOTE = re.compile(r'<blockquote>(.+?)</blockquote>', re.S)
RE_STRIPTAGS = re.compile(r'[ \t]*<.+?>[ \t]*', re.S)


def report(type, exercises, with_solutions=True, base_url='http://localhost'):
    '''
    render pdf/rtf/txt report
    '''
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    text = get_template('report/%s.html' % type).render({
        'exercises': exercises,
        'with_solutions': with_solutions,
        'now': now,
        'base_url': base_url,
    })

    if type == 'pdf':
        fp = StringIO()
        try:
            pdf = pisaDocument(latex2img(text), fp, link_callback=_upfile_path)
            return fp.getvalue()
        except:
            pass
        finally:
            fp.close()
    elif type == 'rtf':
        convetor = HTML2RTF()
        convetor.feed(latex2img(text))
        return convetor.get_rtf()
    else:
        return html2text(text)


# handle uploaded images
def _upfile_path(path, _):
    if path.startswith(settings.MEDIA_URL):
        return os.path.join(settings.MEDIA_ROOT, path[len(settings.MEDIA_URL):])
    return path


def _repl(obj):
    latex = obj.group(0)
    latex = latex[2:-2] if latex[:2] == '$$' else latex[1:-1]
    return '<img src="http://www.forkosh.com/mathtex.cgi?%s" /><latex>(%s)</latex>' % (urllib.quote(latex), latex)


def latex2img(html):
    '''
    find and replace latex expr to html img
    '''
    return RE_LATEX.sub(_repl, html)


def _repl_code(obj):
    return '\n' + '\n'.join('  ' + i for i in obj.group(1).split('\n'))


def _repl_latex(obj):
    latex = obj.group(0)
    latex = latex[2:-2] if latex[:2] == '$$' else latex[1:-1]
    return '\n  {%s}\n' % latex


def _repl_ul(obj):
    lis = obj.group(1)
    return '\n' + RE_LI.sub(r'- \1', lis)


_li_index = 0
def _repl_ol(obj):
    global _li_index
    _li_index = 0
    lis = obj.group(1)
    return '\n' + RE_LI.sub(_repl_li, lis)


def _repl_li(obj):
    global _li_index
    _li_index += 1
    return '%d. %s' % (_li_index, obj.group(1))


def _repl_strip(obj):
    ret = RE_CODE.sub(_repl_code, obj.group(1))
    ret = RE_BLOCKQUOTE.sub(_repl_code, ret)
    ret = RE_LATEX.sub(_repl_latex, ret)
    ret = RE_OL.sub(_repl_ol, ret)
    ret = RE_UL.sub(_repl_ul, ret)
    ret = RE_STRIPTAGS.sub('', ret)
    return ret.replace('\n', '\r\n')


def html2text(html):
    '''
    '''
    return RE_STRIP.sub(_repl_strip, html)


TMPFILE_PREFIX = '/tmp/_ASKBOT_RTF_IMG'
class HTML2RTF(HTMLParser):
    def __init__(self, *a, **b):
        HTMLParser.__init__(self, *a, **b)
        self._doc = PyRTF.Document()
        self._ss = self._doc.StyleSheet
        self._section = self._doc.NewSection()
        self._queue = []
        self._tag = ''

    def handle_starttag(self, tag, attrs):
        self._tag, self._attrs = tag, dict(attrs)
        if tag == 'img':
            src = self._attrs.pop('src', None)
            if src:
                try:
                    self._queue.append(self._img(src))
                except:
                    pass
        elif tag == 'pdf:nextpage':
            self._queue.append(
                PyRTF.ParagraphPS().SetPageBreakBefore(True)
            )

    def handle_endtag(self, tag):
        if tag == 'p':
            self._do_queue()
        self._tag = ''

    def handle_data(self, data):
        t = self._tag
        data = data.encode('utf-8')
        if 'h1' <= t <= 'h3':
            size = [32, 24, 16][int(t[-1]) - 1]
            self._section.append('')
            self._section.append(
                PyRTF.Paragraph(PyRTF.TEXT(data, bold=True, size=size))
            )
        elif t in ('strong', 'b'):
            self._queue.append(PyRTF.B(data))
        elif t in ('i', 'em'):
            self._queue.append(PyRTF.I(data))
        elif t == 'u':
            self._queue.append(PyRTF.U(data))
        elif t == 'code':
            for i in data.split('\n'):
                self._queue.append(
                    PyRTF.Paragraph(PyRTF.TAB,
                        PyRTF.TEXT(i, font=self._ss.Fonts.CourierNew))
                )
        elif t == 'latex':
            self._queue.append(self._center_p(
                PyRTF.TEXT(
                    data,
                    font=self._ss.Fonts.CourierNew,
                    colour=self._ss.Colours.GreyDark
                )
            ))
        elif t == 'blockquote':
            self._queue.append(PyRTF.TAB)
        elif t == 'th':
            # solution
            if data[0] == 'A':
                self._queue.append(PyRTF.TAB)
            self._queue.append(PyRTF.TEXT(data, bold=True))
            self._queue.append(' ')
        elif t == 'p':
            self._queue.append(data)
        elif t not in ('html', 'head', 'style', 'script', 'table', 'tr', 'td', 'th'):
            self._queue.append(data)
        else:
            #print 'Skiping: ', data
            pass

    def _center_p(self, *a):
        p = PyRTF.Paragraph(*a)
        s = self._ss.ParagraphStyles.Normal.Copy()
        s.ParagraphPropertySet.SetAlignment(3) # center
        p.Style = s
        return p

    def _img(self, src):
        p = _upfile_path(src, None)
        if p.startswith(('http://', 'https://', 'ftp://')):
            obj = urllib.urlopen(p)
            ct = obj.headers['Content-Type'].lower()
            if ct[:6] == 'image/' and ct[6:] in ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif'):
                t = ct[6:]
                fname = TMPFILE_PREFIX + '.png'
                open(fname, 'w+').write(obj.read())
                if t != 'png':
                    im = Image.open(fname)
                    im = im.convert('RGB')
                    im.save(fname, 'png')
                return PyRTF.Image(fname)
        return PyRTF.Image(p)

    def _do_queue(self):
        cur_queue = []
        for i in self._queue:
            if isinstance(i, PyRTF.Paragraph):
                self.__do_queue(cur_queue)
                self._section.append(i)
                del cur_queue[:]
            else:
                cur_queue.append(i)
        self.__do_queue(cur_queue)
        del self._queue[:]

    def __do_queue(self, queue):
        if queue:
            p = PyRTF.Paragraph(*queue)
            self._section.append(p)

    def get_rtf(self):
        self._do_queue()
        DR = PyRTF.Renderer()
        fp = StringIO()
        try:
            DR.Write(self._doc, fp)
            return fp.getvalue()
        except:
            pass
        finally:
            fp.close()
