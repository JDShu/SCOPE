#!/usr/bin/env python
# coding: utf-8
# yc@2013/02/22

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

def pdf(exercises, with_answers=True):
    '''
    export to pdf document
    '''
    fp = StringIO()
    html = report_html(exercises, with_answers)
    try:
        pdf = pisaDocument(html, fp, link_callback=_upfile_path)
        return fp.getvalue()
    except:
        pass
    finally:
        fp.close()


def rtf(exercises, with_answers=True):
    '''
    export to rtf
    '''
    html = report_html(exercises, with_answers)
    convetor = HTML2RTF()
    convetor.feed(html)
    return convetor.get_rtf()


def report_html(exercises, with_answers=True):
    '''
    render html report
    '''
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    html = get_template('report/pdf.html').render({
        'exercises': exercises,
        'with_answers': with_answers,
        'now': now,
    })
    return latex2img(html)


# handler uploaded images
def _upfile_path(path, _):
    if path.startswith(settings.MEDIA_URL):
        return os.path.join(settings.MEDIA_ROOT, path[len(settings.MEDIA_URL):])
    return path


def _repl(obj):
    latex = obj.group(0)
    latex = latex[2:-2] if latex[:2] == '$$' else latex[1:-1]
    return '<img src="http://www.forkosh.com/mathtex.cgi?%s" /><code>(%s)</code>' % (urllib.quote(latex), latex)


def latex2img(html):
    '''
    find and replace latex expr to html img
    '''
    return RE_LATEX.sub(_repl, html)


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
        if 'h1' <= t <= 'h3':
            size = [32, 24, 16][int(t[-1]) - 1]
            self._section.append('')
            self._section.append(
                PyRTF.Paragraph(PyRTF.TEXT(data.encode('utf-8'), bold=True, size=size))
            )
        elif t in ('strong', 'b'):
            self._queue.append(PyRTF.B(data.encode('utf-8')))
        elif t in ('i', 'em'):
            self._queue.append(PyRTF.I(data.encode('utf-8')))
        elif t == 'u':
            self._queue.append(PyRTF.U(data.encode('utf-8')))
        elif t == 'pre':
            self._section.append(
                PyRTF.Paragraph(PyRTF.TAB,
                    PyRTF.TEXT(data.encode('utf-8'), font=self._ss.Fonts.CourierNew))
            )
        elif t == 'code':
            self._section.append(self._center_p(
                PyRTF.TEXT(
                    data.encode('utf-8'),
                    font=self._ss.Fonts.CourierNew,
                    colour=self._ss.Colours.GreyDark
                )
            ))
        elif t == 'blockquote':
            self._queue.append(PyRTF.TAB)
        elif t not in ('html', 'head', 'style', 'script', 'table', 'tr', 'td', 'th'):
            self._queue.append(data.encode('utf-8'))
        elif t == 'th':
            # answer
            if data[0] == 'A':
                self._queue.append(PyRTF.TAB)
            self._queue.append(PyRTF.TEXT(data.encode('utf-8'), bold=True))
            self._queue.append(' ')
        elif t == 'p':
            self._queue.append(data.encode('utf-8'))
        else:
            #print 'Skiping: ', data.encode('utf-8')
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
        if self._queue:
            p = PyRTF.Paragraph(*self._queue)
            self._section.append(p)
            del self._queue[:]

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
