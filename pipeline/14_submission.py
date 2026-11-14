# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""T8: fills README.md and submission/project_page.md from submission/templates/ with numbers from docs/data/*.json
(the same keys as the paper, see paper/numbers.md)."""
import importlib
from string import Template
from common import ROOT

paper = importlib.import_module('12_paper')
MAX_SUMMARY_WORDS = 150
SUMMARY = (
    "GroundTwin uses Earth as the twin of the Moon and Mars. First and foremost, our Analog Engine scores all $n_cells land "
    "cells on Earth against a lunar south-pole profile and two Mars crater profiles, using seven features from NASA data. "
    "For each place it shows what matches, what does not, and what Earth can never reproduce. Tested on known analog sites, "
    "it recognised $bt_mars_k of $bt_mars_n Mars analogs in a blind test. Mangystau in Kazakhstan, the floor of a vanished "
    "sea, ranks in the top $mgs_gale% of Earth's land cells for Gale crater. Second, Canada's RCM radar shares the design of "
    "NASA's Mini-RF, so we check radar ice signatures on Earth, where the truth is known. We then combine Mini-RF, LOLA and "
    "Diviner into an Ice Evidence Score for south-pole craters that helps choose where a lunar base could find ice. "
    "Everything is open and traceable to data.")


def main():
    paper.collect()
    N = dict(paper.N)
    N['summary'] = Template(SUMMARY).substitute(N)
    words = len(N['summary'].split())
    assert words <= MAX_SUMMARY_WORDS, f'summary has {words} words'
    for tpl, out in (('README.md', ROOT / 'README.md'), ('project_page.md', ROOT / 'submission' / 'project_page.md')):
        text = Template((ROOT / 'submission' / 'templates' / tpl).read_text(encoding='utf-8')).substitute(N)
        out.write_text(text, encoding='utf-8')
        print('wrote', out.relative_to(ROOT))
    print(f'High-Level Summary: {words} words')


if __name__ == '__main__':
    main()
