// Glyph wallet for the Club Impz web build (game_direction.md: players connect with Glyph on ApeChain).
//
// Glyph's own SDK (@use-glyph/sdk-react) is React-only. Its wagmi connector, glyphWalletConnector(), is a thin
// wrapper around Privy's cross-app wallet with Glyph's Privy app id, so this uses that directly:
// toPrivyWalletProvider() gives a standard EIP-1193 provider, which ui/profile/wallet_bridge.gd treats like
// any browser wallet. Connecting opens Glyph's login window (a popup), so it must start from a click.
//
// Exposes window.impzGlyph = { name, icon, provider() }.
import { completeCrossAppConnectRedirect, toPrivyWalletProvider } from "@privy-io/cross-app-connect";
import { apeChain } from "viem/chains";

// GLYPH_PRIVY_APP_ID in @use-glyph/sdk-react 2.2.9 (STAGING_GLYPH_PRIVY_APP_ID is clxt9p8e601al6tgmsyhu7j3t)
const GLYPH_PRIVY_APP_ID = "cly38x0w10ac945q9yg9sm71i";
const GLYPH_ICON = "https://i.ibb.co/TxcwPQyr/Group-12489-1.png"; // GLYPH_ICON_URL in the SDK

// Glyph answers a login by sending its popup back to this page with the answer in the URL. In that popup this
// hands the answer to the game's tab and closes the popup, so the game must not start there (see head_include).
window.impzGlyphRedirect = completeCrossAppConnectRedirect();

let provider = null;

window.impzGlyph = {
  name: "Glyph",
  icon: GLYPH_ICON,
  chainId: apeChain.id,
  provider() {
    if (!provider) {
      provider = toPrivyWalletProvider({ providerAppId: GLYPH_PRIVY_APP_ID, chains: [apeChain] });
    }
    return provider;
  },
};
