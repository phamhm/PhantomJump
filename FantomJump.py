'''
TODO:
1. automatic search for beginning for word in about 10+/- lines
2. search single character.
3. smarter search
'''
import sublime
import sublime_plugin
from string import digits
from string import ascii_letters
from itertools import permutations


def label_generator_double():
    return (tup[1] + tup[0] for tup in permutations(ascii_letters + digits, 2))


def label_single():
    return (c for c in ascii_letters)


class JumpCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        self.view = self.window.active_view()
        self.orig_target = None
        self.current_cursors = [region for region in self.view.sel()]
        self.labels = dict()

        '''
        SETTINGS:
        '''
        # can be restricted
        self.search_region = self.view.visible_region()

        self.find_flags = None

        self.default_regex_list = {'word': '[\\w\\w]+'}
        self.use_default_regex = False

        if self.use_default_regex:
            pattern = None
            self.generate_targets(pattern)
            self.select_targets()
        else:
            self.window.show_input_panel('Enter regex', '',
                                         self.on_regex_done,
                                         self.on_regex_change,
                                         self.on_cancel)

    def cleanup(self):
        self.view.erase_regions('targets')
        self.view.erase_phantoms('Phantom')

    def on_regex_done(self, input):
        self.select_targets()

    def on_regex_change(self, input):
        if input:
            self.generate_targets(input)
        else:
            self.cleanup()

    def generate_targets(self, regex_input):
        print('generating targets with ' + regex_input)
        regions = self.find_in_view(r'{}'.format(regex_input.strip()))
        self.view.add_regions('targets', regions,
                              'string', '', sublime.DRAW_NO_FILL)

    def find_in_view(self, pattern, flags=None):
        '''
        this will search the whole document.
        DON't move this method out of the class; ST will blow up the call stack
        '''
        if not flags:
            flags = 0

        start_point = self.search_region.begin()
        regions = []

        while(self.search_region and start_point is not None and
              self.search_region.contains(start_point)):
            res = self.view.find(pattern, start_point)

            if res:
                regions.append(res)
                start_point = res.begin() + 1
            else:
                start_point = None

        return regions

    def label_targets(self, miniHTMLformat=None):
        '''
        TODO: miniHTMLformat for adding phantom
        '''
        orig_target = self.view.get_regions('targets')

        self.view.sel().add_all(orig_target)

        if len(orig_target) < 27:
            label_gen = label_single()
        else:
            label_gen = label_generator_double()

        for region in orig_target:
            label = next(label_gen)
            self.labels[label] = region
            self.view.add_phantom("Phantom", region,
                                  '<small class="error">' + label + '</small>',
                                  sublime.LAYOUT_INLINE)
            self.view.sel().clear()

    def select_targets(self):
        self.label_targets()
        self.window.show_input_panel('Enter target', '',
                                     self.on_select_done,
                                     self.on_select_change,
                                     self.on_cancel)

    def on_select_done(self, input):
        regions = self.view.get_regions('targets')
        if regions:
            self.view.sel().clear()
            self.view.sel().add_all(regions)
        else:
            self.view.sel().clear()
            self.view.sel().add_all(self.current_cursors)

        self.cleanup()

    def on_select_change(self, input):
        self.view.erase_regions('targets')
        self.view.sel().clear()

        # input is a comma delimited list
        inlist = [word.strip()
                  for word in input.strip().split(',') if word.strip()]

        if input.strip():
            flag = 0
            regions = [region for label, region in self.labels.items() if any(
                label.startswith(word) for word in inlist)]
        else:
            flag = sublime.DRAW_NO_FILL
            regions = [region for region in self.labels.values()]

        # if blank or no unique targets, then draw empty box
        if len(regions) == 1:
            flag = 0

        self.view.add_regions('targets', regions, 'string', '', flag)

    def on_cancel(self):
        self.cleanup()
        self.view.sel().clear()
        self.view.sel().add_all(self.current_cursors)
