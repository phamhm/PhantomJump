'''
PhantomJump uses ST3 new Phantom and minihtml to
mimic vim's EasyMotion or AceJump
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


class PhantomjumpCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        self.view = self.window.active_view()
        self.orig_target = None
        self.current_cursors = [region for region in self.view.sel()]
        self.labels = dict()

        self.window.show_input_panel('Enter regex', '',
                                     self.on_regex_done,
                                     self.on_regex_change,
                                     self.on_cancel)

    def cleanup(self):
        self.view.erase_regions('targets')
        self.view.erase_phantoms('Phantom')

    def on_regex_change(self, input):
        if input:
            # regions = self.find_all(r'{}'.format(input.strip()))
            regions = self.find_in_view(r'{}'.format(input.strip()))
            self.view.add_regions('targets', regions,
                                  'string', '', sublime.DRAW_NO_FILL)
        else:
            self.cleanup()

    def on_regex_done(self, input):

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
            regions = [region for label, region in self.labels.items() if any(
                label.startswith(word) for word in inlist)]
        else:
            regions = [region for region in self.labels.values()]

        # if blank or no unique targets, then draw empty box
        if len(regions) == 1:
            flag = 0
        elif not input.strip() or len(regions) > 1:
            flag = sublime.DRAW_NO_FILL
        else:
            flag = 0

        self.view.add_regions('targets', regions, 'string', '', flag)

    def find_in_view(self, pattern):
        '''
        this will search the whole document.
        i want to search the
        '''
        visible = self.view.visible_region()
        start_point = visible.begin()
        regions = []
        while(visible and start_point and visible.contains(start_point)):
            res = self.view.find(pattern, start_point)
            if res:
                regions.append(res)
                start_point = res.begin() + 1
            else:
                start_point = None
        return regions

    def find_all(self, pattern):
        '''
        DO NOT USE THIS METHOD
        this method is very bad because it would search the whole file
        '''
        return [region for region in self.view.find_all(pattern)
                if self.view.visible_region().contains(region)]

    def on_cancel(self):
        self.cleanup()
        self.view.sel().clear()
        self.view.sel().add_all(self.current_cursors)
