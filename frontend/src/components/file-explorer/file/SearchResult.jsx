import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import { MaterialReactTable } from "material-react-table";
import prettyBytes from "pretty-bytes";
import Timestamp from "react-timestamp";
import { debounce } from "lodash";
import { ajax } from "../../../utils/generics";
import { getFileIcon } from "../../../utils/file";
import PreviewDialog from "./PreviewDialog";

const FileSearchResult = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchText, setSearchText] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorLoading, setErrorLoading] = React.useState("");
  const [fileList, setFileList] = React.useState([]);
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
        accessorKey: "path",
        header: "Path",
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
        size: 100,
        maxSize: 100,
      },
    ],
    []
  );
  const [openPreviewDialog, setOpenPreviewDialog] = React.useState(false);
  const [fileIdToPreview, setFileIdToPreview] = React.useState(null);

  const loadResult = (value) => {
    if (!value) {
      setFileList([]);
      setErrorLoading("");
      return;
    }

    setIsLoading(true);
    setErrorLoading("");
    ajax
      .get(`/drive/ui-api/files/search`, { params: { keyword: value } })
      .then((response) => setFileList(response.data.values))
      .catch((reason) => {
        setFileList([]);
        setErrorLoading(reason.response.data.error);
      })
      .then(() => setIsLoading(false));
  };

  const loadResultDebounced = React.useCallback(
    debounce((value) => loadResult(value), 500),
    []
  );

  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const keyword = params.get("keyword") || "";
    setSearchText(keyword);
    document.title = "Search results - RPi Drive";
    if (searchText) {
      // Debounce on search text is not empty
      setIsLoading(true);
      setErrorLoading("");
      loadResultDebounced(keyword);
    } else {
      loadResult(keyword);
    }
  }, [location]);

  const openFolder = (fileId) => {
    navigate(`/drive/folder/${fileId}`);
  };

  const handlePreviewDialogClose = () => {
    setOpenPreviewDialog(false);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography color="primary" variant="h5">
        Search results
      </Typography>
      <MaterialReactTable
        columns={columns}
        data={fileList}
        enableRowVirtualization
        enableColumnResizing
        initialState={{
          density: "compact",
          sorting: [{ id: "last_modified", desc: true }],
        }}
        getRowId={(row) => row.id}
        muiTablePaperProps={{
          elevation: 0,
        }}
        muiTableContainerProps={{ sx: { maxHeight: "calc(100vh - 240px)" } }}
        enablePagination={false}
        enableDensityToggle={false}
        enableFullScreenToggle={false}
        enableGlobalFilter={false}
        enableHiding={false}
        state={{
          isLoading: isLoading,
          showAlertBanner: true,
        }}
        layoutMode="grid"
        positionToolbarAlertBanner="bottom"
        muiToolbarAlertBannerProps={
          errorLoading
            ? {
                color: "error",
                children: errorLoading || "Error loading data",
              }
            : {
                color: "success",
                children: `${fileList.length} item(s)`,
              }
        }
        muiTableBodyCellProps={({ cell }) => ({
          onClick: () => {
            const rowData = cell.row.original;
            if (rowData.kind === "folder") {
              openFolder(cell.row.original.id);
            } else {
              setFileIdToPreview(cell.row.original.id);
              setOpenPreviewDialog(true);
            }
          },
          style: { cursor: "pointer" },
        })}
        enableStickyHeader
      />
      {openPreviewDialog && (
        <PreviewDialog
          fileId={fileIdToPreview}
          onClose={handlePreviewDialogClose}
        />
      )}
    </Box>
  );
};

export default FileSearchResult;
