# Host Review Walkthrough Transcript

This transcript outlines the step-by-step commands a host reviewer should run to validate the public review package.

## Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/bmendonca3/authzbench-saas.git
   cd authzbench-saas
   ```

2. **Verify Commit**:
   Ensure you are reviewing the correct candidate commit:
   ```bash
   git log -1
   ```

3. **Install Editable Package**:
   ```bash
   pip install -e .
   ```

4. **Run Public Validation Command**:
   Verify that all public validation checks pass cleanly:
   ```bash
   python3 scripts/validate_public.py --include-scripted-baseline
   ```

5. **Run Host-Presentation Validation**:
   Check that all host-facing links, templates, and schemas are fully compliant:
   ```bash
   python3 scripts/validate_host_presentation.py
   ```

6. **Inspect Dry-Run Bundle**:
   Verify the expected shape of participant submission zips under `platform/kaggle/dry-run-bundle/`.

7. **Build Host Review Bundle**:
   Build the public-safe zip package containing only allowed reviewer documents:
   ```bash
   python3 scripts/build_host_review_bundle.py --check
   ```
