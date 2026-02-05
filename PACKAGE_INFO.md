# Tessara Package Information

## Package Contents

This package contains everything needed to run the Tessara web automation system.

### Core Files

- **codebase/main.py**: Main pipeline orchestration
- **codebase/planner.py**: LLM planner module
- **codebase/scripter.py**: LLM scripter module
- **codebase/answering_llm.py**: Task evaluation module
- **codebase/utils.py**: Utility functions
- **codebase/tessara_ui.py**: Streamlit web UI

### Configuration

- **config.yaml.template**: Configuration template (copy to config.yaml)
- **config.yaml**: Your configuration file (create from template)

### Prompts

- **prompts/planner_instructions.txt**: Instructions for the planner LLM
- **prompts/scripter_instructions.txt**: Instructions for the scripter LLM
- **prompts/answering_instructions.txt**: Instructions for the answering LLM
- **prompts/script_correction_instructions.txt**: Script correction instructions

### Documentation

- **README.md**: Main documentation
- **INSTALL.md**: Detailed installation guide
- **QUICKSTART.md**: Quick start guide
- **PACKAGE_INFO.md**: This file

### Scripts

- **run_ui.bat**: Windows launcher for the UI
- **run_ui.sh**: Linux/Mac launcher for the UI
- **setup.py**: Setup and verification script

### Dependencies

- **requirements.txt**: Python package dependencies

## File Sizes

Approximate sizes:
- Codebase: ~50 KB
- Prompts: ~10 KB
- Documentation: ~20 KB
- Total: ~80 KB (excluding dependencies)

## Version

- **Version**: 1.0
- **Release Date**: February 2025
- **Python Version**: 3.8+

## License

This tool is provided for research purposes.

## Support

For issues or questions:
1. Check README.md for documentation
2. Check INSTALL.md for troubleshooting
3. Verify configuration in config.yaml
4. Run setup.py to verify installation

