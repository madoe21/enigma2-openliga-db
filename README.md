# OpenLigaDB Plugin for Enigma2

This plugin turns the old goal test into a full OpenLigaDB browser + notifier for Enigma2.

## Features

- Browse hierarchy: **Sports → Leagues → Seasons → Matchdays → Matches → Events**
- Event details for goals:
  - minute
  - scorer
  - regular goal / penalty / own goal
  - score
  - teams (short names)
- Background polling service for subscribed leagues or teams
- Two event output services:
  - UI popup
  - LCD/VFD output
- Subscription management (add/remove leagues and teams)
- Settings:
  - output target: UI / LCD / both
  - polling interval
  - message duration
- Info screen with credits, OpenLigaDB source notice, delay notice, and BuyMeACoffee QR reference

## Important Notes

- Data source: **OpenLigaDB**
- OpenLigaDB API docs: https://api.openligadb.de/index.html
- OpenLigaDB website: https://www.openligadb.de
- **Data can be delayed** depending on upstream providers and OpenLigaDB processing.

## Build

The build output is written to the `build` folder.

### Prerequisites

- Linux/WSL build shell with: `make`, `tar`, `ar`
- Optional but recommended: `dos2unix`

### Commands

- Build IPK:
  - `make ipk`
- Deploy to receiver (requires `.env` with `BOX_HOST`, `BOX_PORT`, `BOX_USER`):
  - `make deploy`
- Clean build artifacts:
  - `make clean`

`make ipk` automatically runs a line-ending normalization step (`dos2unix`) before packaging when available.

## Project Structure

- `src/OpenLigaDB` plugin source code
- `src/OpenLigaDB/res` resources
- `src/OpenLigaDB/locale` translations
- `control` package metadata and opkg lifecycle scripts
- `build` generated package artifacts

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Found a bug or have a suggestion for improvement? Please create an issue or pull request.

I appreciate everyone who supports me and the project! For any requests and suggestions, feel free to provide feedback.

<p>
  <a href="https://www.buymeacoffee.com/madoe21">
    <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" height="50" alt="Buy Me a Coffee">
  </a>

  <a href="https://ko-fi.com/madoe21">
    <img src="https://storage.ko-fi.com/cdn/kofi3.png?v=3" height="50" alt="Ko-fi">
  </a>

  <a href="https://paypal.me/MartinD809">
    <img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg" height="50" alt="PayPal">
  </a>
</p>
