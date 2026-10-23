# Security and data-handling notes

- The default provider runs locally with Tesseract OCR. Gemini is opt-in with both `--allow-network` and `--confirm-upload`; it sends selected screenshots to the model provider.
- Never commit or share API keys, `.env` files, private recordings, credentials, or full unreviewed client output. Set `GOOGLE_API_KEY` in your local environment.
- Only included synthetic videos and demo screenshots are intended for public use. Real client material requires authorization and provider data-processing review.
- The `outputs/` and `release-review/` directories are intentionally ignored by Git; inspect any manually added files before publishing.
- Frame references prove *which image* was selected, not that generated semantic claims are correct. Human review is required.
- No external API call is required to run the test suite or view `examples/showcase.html`.
