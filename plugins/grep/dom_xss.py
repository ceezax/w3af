'''
dom_xss.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import re

import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.grep_plugin import GrepPlugin


class dom_xss(GrepPlugin):
    '''
    Grep every page for traces of DOM XSS.

    @author: Andres Riancho ((andres.riancho@gmail.com))
    '''

    JS_FUNCTIONS = ('document.write',
                    'document.writeln',
                    'document.execCommand',
                    'document.open',
                    'window.open',
                    'eval',
                    'window.execScript')
    
    JS_FUNCTION_CALLS = [re.compile(js_f + ' *\((.*?)\)', re.IGNORECASE)
                         for js_f in JS_FUNCTIONS]

    DOM_USER_CONTROLLED = ('document.URL',
                           'document.URLUnencoded',
                           'document.location',
                           'document.referrer',
                           'window.location',
                           )

    def __init__(self):
        GrepPlugin.__init__(self)

        # Compile the regular expressions
        self._scriptRe = re.compile(
            '< *script *>(.*?)</ *script *>', re.IGNORECASE | re.DOTALL)

    def grep(self, request, response):
        '''
        Plugin entry point, search for the DOM XSS vulns.
        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        if not response.is_text_or_html():
            return

        for vuln_code in self._smart_grep(response):
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.add_to_highlight(vuln_code)
            v.set_url(response.get_url())
            v.set_id(response.id)
            v.set_severity(severity.LOW)
            v.set_name('DOM Cross site scripting (Risky JavaScript Code)')
            msg = 'The URL: "' + v.get_url(
            ) + '" has a DOM XSS (Risky JavaScript Code) '
            msg += 'bug using: "' + vuln_code + '".'
            v.set_desc(msg)
            kb.kb.append(self, 'dom_xss', v)

    def _smart_grep(self, response):
        '''
        Search for the DOM XSS vulns using smart grep (context regex).
        @param response: The HTTP response object
        @return: list of dom xss items
        '''
        res = []
        match = self._scriptRe.search(response.get_body())

        if not match:
            return res

        for script_code in match.groups():
            for function_re in self.JS_FUNCTION_CALLS:
                parameters = function_re.search(script_code)
                if parameters:
                    for user_controlled in self.DOM_USER_CONTROLLED:
                        if user_controlled in parameters.groups()[0]:
                            res.append(user_controlled)
        return res

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(kb.kb.get('dom_xss', 'dom_xss'), None)

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for traces of DOM XSS.

        Two configurable parameters exist:
            - simpleGrep
            - smartGrep

        An interesting paper about DOM XSS
        can be found here:
            - http://www.webappsec.org/projects/articles/071105.shtml
        '''
