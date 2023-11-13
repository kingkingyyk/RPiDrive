import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import MiniExplorer from "../mini-explorer";
import Typography from "@mui/material/Typography";
import Select from "@mui/material/Select";

import { ajax } from "../../../utils/generics";

const MoveDialog = (props) => {
  const { volumeId, files, onClose } = props;
  const wideView = useMediaQuery("(min-width:600px)");
  const [selectedVolumeId, setSelectedVolumeId] = React.useState(volumeId);
  const [folderId, setFolderId] = React.useState(null);
  const [strategy, setStrategy] = React.useState("rename");
  const strategies = React.useMemo(
    () => [
      {
        name: "Rename",
        value: "rename",
      },
      {
        name: "Overwrite",
        value: "overwrite",
      },
    ],
    []
  );
  const [volumes, setVolumes] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorText, setErrorText] = React.useState("");

  const loadVolumes = () => {
    ajax
      .get(`/drive/ui-api/volumes`)
      .then((response) => {
        setVolumes(response.data.values);
      })
      .catch(() => onClose(false));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  React.useEffect(() => loadVolumes(), [files]);

  const handleMove = () => {
    const data = {
      files: files,
      strategy: strategy,
      move_to: folderId,
    };

    setIsLoading(true);
    ajax
      .post(`/drive/ui-api/files/move`, data)
      .then(() => onClose(true))
      .catch((reason) => setErrorText(reason.response.data.error))
      .finally(() => setIsLoading(false));
  };

  return (
    <Dialog open fullWidth fullScreen={!wideView}>
      <DialogTitle
        color="primary"
        sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}
      >
        <LocalShippingIcon size="small" />
        Move files
      </DialogTitle>
      <DialogContent>
        <FormControl fullWidth size="small" sx={{ mt: 1 }}>
          <InputLabel id="volume-label">Volume</InputLabel>
          <Select
            labelId="volume-label"
            value={selectedVolumeId}
            label="Volume"
            onChange={(event) => setSelectedVolumeId(event.target.value)}
            MenuProps={{
              MenuListProps: { dense: true },
            }}
          >
            {volumes.map((v) => (
              <MenuItem value={v.id} key={v.id}>
                {v.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl fullWidth size="small" sx={{ mt: 1 }}>
          <InputLabel id="strategy-label">Strategy</InputLabel>
          <Select
            labelId="strategy-label"
            value={strategy}
            label="Strategy"
            onChange={(event) => setStrategy(event.target.value)}
            MenuProps={{
              MenuListProps: { dense: true },
            }}
          >
            {strategies.map((s) => (
              <MenuItem value={s.value} key={s.value}>
                {s.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <MiniExplorer
          volumeId={selectedVolumeId}
          blockedFolders={files}
          onSelect={(folderId) => setFolderId(folderId)}
          onError={() => onClose(false)}
        />
      </DialogContent>
      <DialogActions>
        <Typography variant="subtitle2" color="error">
          {errorText}
        </Typography>
        <Button
          size="small"
          disabled={!folderId || isLoading}
          onClick={handleMove}
        >
          Move
        </Button>
        <Button
          size="small"
          disabled={isLoading}
          onClick={() => onClose(false)}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

MoveDialog.propTypes = {
  volumeId: PropTypes.string.isRequired,
  files: PropTypes.arrayOf(PropTypes.string).isRequired,
  onClose: PropTypes.func.isRequired,
};

export default MoveDialog;
