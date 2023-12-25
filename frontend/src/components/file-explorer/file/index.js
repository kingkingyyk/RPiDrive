import React from "react";
import {
  Link as RouterLink,
  useNavigate,
  useParams,
  useOutletContext,
} from "react-router-dom";
import useMediaQuery from "@mui/material/useMediaQuery";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import ListItemText from "@mui/material/ListItemText";
import ListItemIcon from "@mui/material/ListItemIcon";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Breadcrumbs from "@mui/material/Breadcrumbs";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import FolderIcon from "@mui/icons-material/Folder";
import ShareIcon from "@mui/icons-material/Share";
import CompressIcon from "@mui/icons-material/Compress";
import DriveFileRenameOutlineIcon from "@mui/icons-material/DriveFileRenameOutline";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";

import { MaterialReactTable } from "material-react-table";
import prettyBytes from "pretty-bytes";
import Timestamp from "react-timestamp";
import { ajax } from "../../../utils/generics";
import { getFileIcon } from "../../../utils/file";
import PreviewDialog from "./PreviewDialog";
import ShareDialog from "./ShareDialog";
import CompressDialog from "./CompressDialog";
import RenameDialog from "./RenameDialog";
import MoveDialog from "./MoveDialog";
import DeleteDialog from "./DeleteDialog";

const File = () => {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [triggerLoad, setTriggerLoad] = useOutletContext();
  const wideView = useMediaQuery("(min-width:600px)");
  const [isLoading, setIsLoading] = React.useState(true);
  const [errorLoading, setErrorLoading] = React.useState("");
  const [file, setFile] = React.useState({});
  const [fileList, setFileList] = React.useState([]);
  const [paths, setPaths] = React.useState([]);
  const [expandPathAnchor, setExpandPathAnchor] = React.useState(null);
  const columns = React.useMemo(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        Cell: ({ cell }) => (
          <React.Fragment>
            {getFileIcon(cell.row.original)}
            <Typography variant="inherit" sx={{ ml: 1 }}>
              {cell.getValue()}
            </Typography>
          </React.Fragment>
        ),
      },
      {
        accessorKey: "last_modified",
        header: "Last modified",
        Cell: ({ cell }) => (
          <Tooltip title={<Timestamp date={cell.getValue()} />}>
            <span>
              <Timestamp relative date={cell.getValue()} autoUpdate />
            </span>
          </Tooltip>
        ),
        enableColumnFilter: false,
        enableResizing: false,
        size: 100,
        maxSize: 100,
      },
      {
        accessorKey: "size",
        header: "File size",
        Cell: ({ cell }) => {
          return cell.row.original.kind === "folder"
            ? "-"
            : prettyBytes(cell.getValue());
        },
        enableColumnFilter: false,
        enableResizing: false,
        size: 100,
        maxSize: 100,
      },
    ],
    []
  );
  const [rowSelection, setRowSelection] = React.useState({});
  const [fileIdToShare, setFileIdToShare] = React.useState("");
  const [openPreviewDialog, setOpenPreviewDialog] = React.useState(false);
  const [fileIdToPreview, setFileIdToPreview] = React.useState(null);
  const [openShareDialog, setOpenShareDialog] = React.useState(false);
  const [filesToCompress, setFilesToCompress] = React.useState([]);
  const [openCompressDialog, setOpenCompressDialog] = React.useState(false);
  const [fileToRename, setFileToRename] = React.useState(null);
  const [openRenameDialog, setOpenRenameDialog] = React.useState(false);
  const [filesToMove, setFilesToMove] = React.useState([]);
  const [openMoveDialog, setOpenMoveDialog] = React.useState(false);
  const [filesToDelete, setFilesToDelete] = React.useState([]);
  const [openDeleteDialog, setOpenDeleteDialog] = React.useState(false);
  const [contextMenu, setContextMenu] = React.useState(null);

  const loadFile = () => {
    const params = {
      fields: "volume,path,children",
    };

    setIsLoading(true);
    setErrorLoading("");
    ajax
      .get(`/drive/ui-api/files/${fileId}`, { params: params })
      .then((response) => {
        setFile(response.data);
        setFileList(response.data.children);

        response.data.path.push({
          id: fileId,
          name: response.data.name,
        });
        // Set root folder to volume name
        response.data.path[0].name = response.data.volume.name;
        setPaths(response.data.path);
        document.title =
          (response.data.name || response.data.volume.name) + " - RPi Drive";
      })
      .catch((reason) => setErrorLoading(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    setRowSelection({});
    loadFile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId, triggerLoad]);

  const handleExpandPath = (event) => {
    setExpandPathAnchor(event.currentTarget);
  };

  const handleCloseExpandPath = () => {
    setExpandPathAnchor(null);
  };

  const openFolder = (fileId) => {
    setExpandPathAnchor(null);
    navigate(`/drive/folder/${fileId}`);
  };

  const renderPath = React.useMemo(() => {
    let collapsedPaths = [];
    let shownPaths = [];

    if (paths.length > 3) {
      collapsedPaths = paths.slice(0, paths.length - 2);
      shownPaths = paths.slice(2);
    } else {
      shownPaths = [...paths];
    }

    return (
      <Breadcrumbs
        separator={<NavigateNextIcon fontSize="small" />}
        sx={{ mt: wideView ? 0 : 2 }}
      >
        {collapsedPaths.length > 0 && (
          <Box>
            <IconButton onClick={handleExpandPath} size="large">
              <MoreHorizIcon />
            </IconButton>
            <Menu
              anchorEl={expandPathAnchor}
              open={expandPathAnchor !== null}
              onClose={handleCloseExpandPath}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "left",
              }}
              transformOrigin={{
                vertical: "top",
                horizontal: "left",
              }}
              MenuListProps={{ dense: true }}
            >
              {collapsedPaths.map((folder) => (
                <MenuItem key={folder.id} onClick={() => openFolder(folder.id)}>
                  <ListItemIcon>
                    <FolderIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText>{folder.name}</ListItemText>
                </MenuItem>
              ))}
            </Menu>
          </Box>
        )}
        {shownPaths.map((path) => (
          <Button
            variant="text"
            key={path.id}
            size="large"
            component={RouterLink}
            to={`/drive/folder/${path.id}`}
            sx={{ textTransform: "none" }}
          >
            {path.name}
          </Button>
        ))}
      </Breadcrumbs>
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paths, expandPathAnchor, wideView]);

  const handlePreviewDialogClose = () => {
    setOpenPreviewDialog(false);
  };

  const handleShareDialogClose = () => {
    setOpenShareDialog(false);
  };

  const handleCompressDialogClose = (flag) => {
    setOpenCompressDialog(false);
    if (flag) {
      setTriggerLoad(!triggerLoad);
    }
  };

  const handleRenameDialogClose = (flag) => {
    setOpenRenameDialog(false);
    if (flag) {
      loadFile();
    }
  };

  const handleMoveDialogClose = (flag) => {
    setOpenMoveDialog(false);
    if (flag) {
      setRowSelection({});
      loadFile();
    }
  };

  const handleDeleteDialogClose = (flag) => {
    setOpenDeleteDialog(false);
    if (flag) {
      setRowSelection({});
      loadFile();
    }
  };

  const handleContextMenuOpen = (event, file) => {
    event.preventDefault();

    let selectedFileIds = Object.keys(rowSelection).filter(
      (x) => rowSelection[x]
    );
    if (!rowSelection[file.id]) {
      setRowSelection({ [file.id]: true });
      selectedFileIds = [file.id];
    }
    selectedFileIds = new Set(selectedFileIds);

    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX + 2,
            mouseY: event.clientY - 6,
            files: fileList.filter((x) => selectedFileIds.has(x.id)),
          }
        : null
    );
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
  };

  const renderContextMenu = React.useMemo(
    () => (
      <Menu
        open={contextMenu !== null}
        onClose={handleContextMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
        MenuListProps={{ dense: true }}
      >
        <MenuItem
          disabled={!contextMenu || contextMenu.files.length > 1}
          onClick={() => {
            handleContextMenuClose();
            setFileIdToShare(contextMenu.files[0].id);
            setOpenShareDialog(true);
          }}
        >
          <ListItemIcon>
            <ShareIcon />
          </ListItemIcon>
          <ListItemText>Share</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!contextMenu}
          onClick={() => {
            handleContextMenuClose();
            setFilesToCompress(contextMenu.files.map((x) => x.id));
            setOpenCompressDialog(true);
          }}
        >
          <ListItemIcon>
            <CompressIcon />
          </ListItemIcon>
          <ListItemText>Compress</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!contextMenu || contextMenu.files.length > 1}
          onClick={() => {
            handleContextMenuClose();
            setFileToRename(contextMenu.files[0]);
            setOpenRenameDialog(true);
          }}
        >
          <ListItemIcon>
            <DriveFileRenameOutlineIcon />
          </ListItemIcon>
          <ListItemText>Rename</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!contextMenu}
          onClick={() => {
            handleContextMenuClose();
            setFilesToMove(contextMenu.files.map((x) => x.id));
            setOpenMoveDialog(true);
          }}
        >
          <ListItemIcon>
            <LocalShippingIcon />
          </ListItemIcon>
          <ListItemText>Move</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!contextMenu}
          onClick={() => {
            handleContextMenuClose();
            setFilesToDelete(contextMenu.files);
            setOpenDeleteDialog(true);
          }}
        >
          <ListItemIcon>
            <DeleteForeverIcon color="error" />
          </ListItemIcon>
          <ListItemText color="error">Delete</ListItemText>
        </MenuItem>
      </Menu>
    ),
    [contextMenu]
  );

  return (
    <Box>
      {renderPath}
      <MaterialReactTable
        columns={columns}
        data={fileList}
        enableRowSelection
        enableRowVirtualization
        positionActionsColumn="last"
        enableColumnResizing
        initialState={{
          density: "compact",
        }}
        getRowId={(row) => row.id}
        muiTablePaperProps={{
          elevation: 0,
        }}
        muiTableContainerProps={{ sx: { maxHeight: "calc(100vh - 280px)" } }}
        enablePagination={false}
        enableDensityToggle={false}
        enableFullScreenToggle={false}
        muiToolbarAlertBannerProps={
          errorLoading
            ? {
                color: "error",
                children: errorLoading || "Error loading data",
              }
            : {
                color: "info",
                children: `${fileList.length} item(s)`,
              }
        }
        muiTableBodyCellProps={({ cell }) => ({
          onClick: (event) => {
            const rowData = cell.row.original;
            if (rowData.kind === "folder") {
              openFolder(cell.row.original.id);
            } else {
              setFileIdToPreview(cell.row.original.id);
              setOpenPreviewDialog(true);
            }
          },
          onContextMenu: (event) =>
            handleContextMenuOpen(event, cell.row.original),
          style: { cursor: "pointer" },
        })}
        enableHiding={false}
        state={{
          isLoading: isLoading,
          rowSelection: rowSelection,
          showAlertBanner: true,
        }}
        enableGlobalFilter={false}
        positionToolbarAlertBanner="bottom"
        displayColumnDefOptions={{
          "mrt-row-select": { size: 24, maxSize: 24 },
          "mrt-row-actions": { size: 48, maxSize: 48 },
        }}
        onRowSelectionChange={setRowSelection}
        renderTopToolbarCustomActions={({ table }) => {
          let selectionCount = Object.values(rowSelection).filter(
            (x) => x
          ).length;
          return (
            <Box sx={{ display: "flex", gap: "1rem" }}>
              <Tooltip title="Compress">
                <IconButton
                  size="small"
                  onClick={() => {
                    setFilesToCompress(
                      Object.keys(rowSelection).filter((x) => rowSelection[x])
                    );
                    setOpenCompressDialog(true);
                  }}
                  disabled={selectionCount === 0}
                >
                  <CompressIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Move">
                <IconButton
                  size="small"
                  onClick={() => {
                    setFilesToMove(
                      Object.keys(rowSelection).filter((x) => rowSelection[x])
                    );
                    setOpenMoveDialog(true);
                  }}
                  disabled={selectionCount === 0}
                >
                  <LocalShippingIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => {
                    const selectedIds = new Set(
                      Object.keys(rowSelection).filter((x) => rowSelection[x])
                    );
                    setFilesToDelete(
                      fileList.filter((x) => selectedIds.has(x.id))
                    );
                    setOpenDeleteDialog(true);
                  }}
                  disabled={selectionCount === 0}
                >
                  <DeleteForeverIcon />
                </IconButton>
              </Tooltip>
            </Box>
          );
        }}
        enableStickyHeader
      />
      {openPreviewDialog && (
        <PreviewDialog
          fileId={fileIdToPreview}
          onClose={handlePreviewDialogClose}
        />
      )}
      {openShareDialog && (
        <ShareDialog fileId={fileIdToShare} onClose={handleShareDialogClose} />
      )}
      {openCompressDialog && (
        <CompressDialog
          volumeId={file.volume.id}
          initialName={`${file.name || file.volume.name}.zip`}
          files={filesToCompress}
          onClose={handleCompressDialogClose}
        />
      )}
      {openRenameDialog && (
        <RenameDialog file={fileToRename} onClose={handleRenameDialogClose} />
      )}
      {openMoveDialog && (
        <MoveDialog
          volumeId={file.volume.id}
          files={filesToMove}
          onClose={handleMoveDialogClose}
        />
      )}
      {openDeleteDialog && (
        <DeleteDialog files={filesToDelete} onClose={handleDeleteDialogClose} />
      )}
      {renderContextMenu}
    </Box>
  );
};

export default File;
