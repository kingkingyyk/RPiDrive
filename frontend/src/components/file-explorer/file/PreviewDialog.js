import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Grid from "@mui/material/Grid";
import Skeleton from "@mui/material/Skeleton";
import Typography from "@mui/material/Typography";

import Editor from "@monaco-editor/react";
import { ajax } from "../../../utils/generics";

const PreviewDialog = (props) => {
  const { fileId, onClose } = props;
  const wideView = useMediaQuery("(min-width:600px)");
  const downloadLink = `/drive/download/${fileId}`;
  const thumbnailLink = `/drive/ui-api/files/${fileId}/thumbnail`;
  const [file, setFile] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [fileText, setFileText] = React.useState("");

  React.useEffect(() => {
    if (file && file.media_type.startsWith("text/")) {
      ajax
        .get(downloadLink)
        .then((response) => {
          setFileText(response.data);
        })
        .catch(() => {
          onClose();
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  const loadFileInfo = () => {
    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/files/${fileId}`)
      .then((response) => {
        setFile(response.data);
      })
      .catch(() => {
        onClose();
      })
      .then(() => setIsLoading(false));
  };

  React.useEffect(() => {
    if (fileId) {
      loadFileInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId]);

  const handleDownload = () => {
    window.open(downloadLink, "_blank");
  };

  const renderPreview = () => {
    if (!file.media_type) {
      return <Typography variant="subtitle2">No preview available</Typography>;
    }
    if (file.media_type.startsWith("audio")) {
      return (
        <Box sx={{ pl: 1, pr: 1 }}>
          <Grid container spacing={2}>
            <Grid item>
              <img
                src={thumbnailLink}
                style={{ height: "64px" }}
                onLoad={(event) => (event.target.style.display = "unset")}
                onError={(event) => (event.target.style.display = "none")}
                loading="lazy"
                alt="Album art"
              />
            </Grid>
            <Grid item>
              <Typography variant="body1">
                {file?.metadata?.title || "-"}
              </Typography>
              <Typography variant="body1">
                {file?.metadata?.artist || "-"} - {file?.metadata?.album || "-"}
              </Typography>
            </Grid>
          </Grid>
          <audio controls autoplay="" loop style={{ width: "100%" }}>
            <source src={downloadLink} type={file.media_type} />
          </audio>
        </Box>
      );
    }
    if (file.media_type.startsWith("video")) {
      return (
        <video controls autoplay="" loop style={{ width: "100%" }}>
          <source src={downloadLink} type={file.media_type} />
        </video>
      );
    }
    if (file.media_type.startsWith("image")) {
      return (
        <Box>
          <img
            src={downloadLink}
            style={{
              height: "100%",
              maxHeight: "80vh",
              width: "auto",
              display: "block",
              marginLeft: "auto",
              marginRight: "auto",
            }}
            alt="Preview"
          />
        </Box>
      );
    }
    if (file.media_type === "application/pdf") {
      return (
        <embed
          src={downloadLink}
          type={file.media_type}
          style={{ width: "100%" }}
        />
      );
    }
    if (file.media_type.startsWith("text")) {
      const languageMap = {
        "text/x-python": "python",
        "text/javascript": "javascript",
        "text/x-java": "java",
        "text/x-c++src": "cpp",
        "text/css": "css",
      };
      return (
        <Box sx={{ border: "1px solid gray" }}>
          <Editor
            height="60vh"
            defaultLanguage={languageMap[file.media_type] || "text"}
            value={fileText}
            options={{ readOnly: true, theme: "vs-dark" }}
          />
        </Box>
      );
    }
    return <Typography variant="subtitle2">No preview available</Typography>;
  };

  return (
    <Dialog open onClose={onClose} fullWidth fullScreen={!wideView}>
      <DialogTitle
        color="primary"
        sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}
      >
        {!file || isLoading ? <Skeleton /> : file.name}
      </DialogTitle>
      <DialogContent>{file && renderPreview()}</DialogContent>
      <DialogActions>
        <Button size="small" onClick={handleDownload}>
          Download
        </Button>
        <Button size="small" onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

PreviewDialog.propTypes = {
  fileId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default PreviewDialog;
