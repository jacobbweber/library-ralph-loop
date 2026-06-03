# Ralph Loop Development Plan & Roadmap

## 🎯 Current Focus
- **Tool Creation**: Create core tools (`librarian.py`, `archivist.py`) and templates.

## 📋 Active Tasks Queue
1. [x] Run `.\dev\tools\env_check.ps1` to verify Python 3.8+ availability.
2. [ ] Run `python dev/tools/librarian.py --run-tests` to ensure tools are functioning correctly.
3. [ ] Run `python dev/tools/librarian.py` to validate metadata linting passes on templates.
4. [ ] Promote all core tools and templates to `prod/` using `archivist.py`.
5. [ ] Run the first dynamic index rebuild on production using `python prod/tools/cataloger.py --dir prod/library`.
6. [ ] Execute initial web research on digital library structures and cataloging systems.

## 🔬 Research Queue & Ideas
- **Topic 1**: Digital Wiki structures for low-context lookup strategies (Zettelkasten vs Concept Mapping).
- **Topic 2**: Strategies for local LLM text summarization formats (DIKW vs Cornell retrieval cues).
- **Topic 3**: Automatic tag extraction algorithms using simple term frequency.

## 📊 Self-Monitoring & Benchmarks
- **Last Status**: Tools created.
- **Accuracy Rate**: 100% (Baseline)
- **Token Efficiency (CEI)**: 0 (No lookups yet)
- **Average Cycle Turnaround Time (CTT)**: 0s
