# Package Checklist

Use this checklist to verify the package is complete before distribution.

## Core Files
- [x] codebase/main.py
- [x] codebase/planner.py
- [x] codebase/scripter.py
- [x] codebase/answering_llm.py
- [x] codebase/utils.py
- [x] codebase/tessara_ui.py

## Configuration
- [x] config.yaml.template
- [ ] config.yaml (user creates from template)

## Prompts
- [x] prompts/planner_instructions.txt
- [x] prompts/scripter_instructions.txt
- [x] prompts/answering_instructions.txt
- [x] prompts/script_correction_instructions.txt

## Documentation
- [x] README.md
- [x] INSTALL.md
- [x] QUICKSTART.md
- [x] PACKAGE_INFO.md
- [x] CHANGELOG.md
- [x] LICENSE

## Scripts
- [x] run_ui.bat (Windows)
- [x] run_ui.sh (Linux/Mac)
- [x] setup.py

## Dependencies
- [x] requirements.txt

## Other
- [x] .gitignore
- [x] responses/ directory (empty, created automatically)

## Verification Steps

1. **File Structure**: All files listed above are present
2. **Dependencies**: requirements.txt contains all necessary packages
3. **Configuration**: config.yaml.template is complete and clear
4. **Documentation**: README.md explains how to use the system
5. **Scripts**: run_ui.bat and run_ui.sh are executable
6. **Code**: All Python files are syntactically correct
7. **Prompts**: All prompt files are present and readable

## Testing Checklist

Before distributing, test:
- [ ] Installation from scratch works
- [ ] UI launches successfully
- [ ] Configuration file can be created from template
- [ ] All imports work correctly
- [ ] Playwright browsers install correctly
- [ ] Basic automation task runs successfully

## Distribution Checklist

Before sharing:
- [ ] Remove any personal API keys from config.yaml.template
- [ ] Remove any test files or temporary files
- [ ] Verify .gitignore is working
- [ ] Create a zip/tar archive
- [ ] Test archive extraction
- [ ] Verify all files are included in archive

