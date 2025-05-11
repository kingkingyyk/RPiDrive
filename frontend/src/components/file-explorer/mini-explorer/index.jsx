import React from "react";
import PropTypes from "prop-types";

import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Skeleton from "@mui/material/Skeleton";
import FolderIcon from "@mui/icons-material/Folder";
import Typography from "@mui/material/Typography";
import DescriptionIcon from "@mui/icons-material/Description";

import { ajax } from "../../../utils/generics";

const MiniExplorer = (props) => {
  const { volumeId, blockedFolders, onSelect, onError, sx } = props;
  const [volumeName, setVolumeName] = React.useState("");
  const [currFolder, setCurrFolder] = React.useState(null);
  const [path, setPath] = React.useState("");
  const blockedFoldersSet = new Set(blockedFolders);

  const selectFile = (volName, fileId) => {
    ajax
      .get(`/drive/ui-api/files/${fileId}`, {
        params: { fields: "children,parent,path" },
      })
      .then((response) => {
        setCurrFolder(response.data);

        let pList = response.data.path.map((x) => x.name);
        pList[0] = volName;
        pList.push(response.data.name);
        setPath(pList.join("/"));

        onSelect(fileId);
      })
      .catch(() => onError());
  };

  const loadRoot = () => {
    ajax
      .get(`/drive/ui-api/volumes/${volumeId}`)
      .then((response) => {
        setVolumeName();
        selectFile(response.data.name, response.data.root_file);
      })
      .catch(() => onError());
  };

  React.useEffect(() => loadRoot(), [volumeId]);

  if (currFolder === null) {
    return <Skeleton variant="rounded" height={60} />;
  }
  return (
    <React.Fragment>
      <Box sx={{ display: "flex", flexFlow: "row", alignItems: "center" }}>
        <IconButton
          size="small"
          color="primary"
          disabled={!currFolder.parent}
          onClick={() => selectFile(volumeName, currFolder.parent.id)}
        >
          <KeyboardArrowUpIcon />
        </IconButton>
        <Typography variant="subtitle2">{path}</Typography>
      </Box>
      <Box sx={sx}>
        <List dense>
          {currFolder.children.map((file) => (
            <ListItemButton
              key={file.id}
              disabled={
                file.kind !== "folder" || blockedFoldersSet.has(file.id)
              }
              disablePadding
              onClick={() => selectFile(volumeName, file.id)}
            >
              <ListItemIcon>
                {file.kind === "folder" ? <FolderIcon /> : <DescriptionIcon />}
              </ListItemIcon>
              <ListItemText primary={file.name} />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </React.Fragment>
  );
};

MiniExplorer.propTypes = {
  volumeId: PropTypes.string.isRequired,
  blockedFolders: PropTypes.arrayOf(PropTypes.string).isRequired,
  onSelect: PropTypes.func.isRequired,
  onError: PropTypes.func.isRequired,
  sx: PropTypes.object,
};

export default MiniExplorer;
