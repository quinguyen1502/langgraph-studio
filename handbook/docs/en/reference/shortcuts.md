# Keyboard shortcuts

++ctrl++ is ++cmd++ on macOS. ++question++ or ++ctrl+slash++ shows this list in
the editor. The registry is `frontend/src/lib/shortcuts.ts`, shared by the key
handler, the cheat sheet and the command palette.

| Group | Action | Keys | While typing |
| --- | --- | --- | --- |
| General | Save | ++ctrl+s++ | yes |
| General | Command palette | ++ctrl+k++ | yes |
| General | Shortcut sheet | ++question++, ++ctrl+slash++ | |
| General | Clear selection / close panel | ++esc++ | |
| Run | Run | ++ctrl+enter++ | yes |
| Run | Stop | ++ctrl+period++ | yes |
| History | Undo | ++ctrl+z++ | |
| History | Redo | ++ctrl+shift+z++, ++ctrl+y++ | |
| Clipboard | Copy, cut, paste nodes | ++ctrl+c++, ++ctrl+x++, ++ctrl+v++ | |
| Clipboard | Duplicate | ++ctrl+d++ | |
| Canvas | Delete selection | ++delete++, ++backspace++ | |
| Canvas | Select all | ++ctrl+a++ | |
| Canvas | Fit view | ++shift+1++ | |
| Canvas | Zoom in, out | ++ctrl+equal++, ++ctrl+minus++ | |
| Canvas | Tidy up the layout | ++shift+l++ | |

Shortcuts other than save, run, stop and the palette are ignored while you
type in a field, and an open dialog disables them. Text fields keep their
native undo and copy.
