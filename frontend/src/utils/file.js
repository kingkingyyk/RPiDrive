import AudiotrackIcon from "@mui/icons-material/Audiotrack";
import MovieIcon from "@mui/icons-material/Movie";
import ImageIcon from "@mui/icons-material/Image";
import BookIcon from "@mui/icons-material/Book";
import CodeIcon from "@mui/icons-material/Code";
import FolderZipIcon from "@mui/icons-material/FolderZip";
import WebAssetIcon from "@mui/icons-material/WebAsset";
import FolderIcon from "@mui/icons-material/Folder";
import DescriptionIcon from "@mui/icons-material/Description";

import { blue, green, purple, red, orange } from "@mui/material/colors";

const books = new Set([
  "application/pdf",
  "application/epub",
  "application/mobi",
]);

export const getFileIcon = (file) => {
  if (file.kind === "folder") return <FolderIcon size="small" color="action" />;
  if (file.media_type) {
    if (file.media_type.startsWith("audio/"))
      return <AudiotrackIcon size="small" style={{ color: purple[500] }} />;
    if (file.media_type.startsWith("video/"))
      return <MovieIcon size="small" style={{ color: red[600] }} />;
    if (file.media_type.startsWith("image/"))
      return <ImageIcon size="small" style={{ color: red[600] }} />;
    if (file.media_type.startsWith("text/")) {
      return <CodeIcon size="small" />;
    }
    if (file.media_type === "application/zip") {
      return <FolderZipIcon size="small" style={{ color: orange[500] }} />;
    }
    if (file.name.toLowerCase().endsWith(".exe")) {
      return <WebAssetIcon size="small" color="primary" />;
    }
    if (books.has(file.media_type)) {
      return <BookIcon size="small" style={{ color: green[600] }} />;
    }
  }

  return <DescriptionIcon size="small" style={{ color: blue[600] }} />;
};
