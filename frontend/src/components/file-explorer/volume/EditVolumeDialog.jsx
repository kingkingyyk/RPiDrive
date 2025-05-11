import React from "react";
import PropTypes from "prop-types";
import useMediaQuery from "@mui/material/useMediaQuery";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";
import Box from "@mui/material/Box";
import Select from "@mui/material/Select";
import Skeleton from "@mui/material/Skeleton";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";

import { ajax } from "../../../utils/generics";

const EditVolumeDialog = (props) => {
  const wideView = useMediaQuery("(min-width:600px)");
  const [kinds, setKinds] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(false);

  const [name, setName] = React.useState("");
  const [kind, setKind] = React.useState("");
  const kindFixed = Boolean(props.id);
  const [path, setPath] = React.useState("");

  const [isApplying, setIsApplying] = React.useState(false);
  const [applyError, setApplyError] = React.useState("");

  const loadKind = () => {
    ajax
      .get("/drive/ui-api/volumes/kinds")
      .then((response) => {
        setKinds(response.data.values);
        if (!kind) {
          setKind(response.data.values[0].value);
        }
      })
      .catch(() => {
        handleClose();
      });
  };

  const loadVolume = () => {
    if (!props.id) return;

    setIsLoading(true);
    ajax
      .get(`/drive/ui-api/volumes/${props.id}`)
      .then((response) => {
        let volume = response.data;
        setName(volume.name);
        setKind(volume.kind);
        setPath(volume.path);
      })
      .catch(() => {
        handleClose();
      })
      .finally(() => setIsLoading(false));
  };

  React.useEffect(() => {
    loadKind();
    loadVolume();
  }, [props.id]);

  const handleApply = () => {
    if (props.id) {
      const postData = {
        name: name,
        path: path,
      };
      setIsApplying(true);
      setApplyError("");

      ajax
        .post(`/drive/ui-api/volumes/${props.id}`, postData)
        .then(() => {
          props.onClose(true);
        })
        .catch((reason) => {
          setApplyError(reason.response.data.error);
        })
        .finally(() => setIsApplying(false));
    } else {
      const postData = {
        name: name,
        kind: kind,
        path: path,
      };
      setIsApplying(true);
      setApplyError("");

      ajax
        .post(`/drive/ui-api/volumes/create`, postData)
        .then(() => {
          props.onClose(true);
        })
        .catch((reason) => {
          setApplyError(reason.response.data.error);
        })
        .finally(() => setIsApplying(false));
    }
  };

  const handleClose = () => {
    props.onClose(false);
  };

  return (
    <Dialog open={props.open} fullScreen={!wideView} fullWidth maxWidth="xl">
      <DialogTitle>{props.id ? "Edit" : "Create"} volume</DialogTitle>
      <DialogContent>
        {isLoading ? (
          <React.Fragment>
            <Skeleton variant="text" sx={{ fontSize: "1rem" }} />
            <Skeleton variant="text" sx={{ fontSize: "1rem" }} />
            <Skeleton variant="text" sx={{ fontSize: "1rem" }} />
          </React.Fragment>
        ) : (
          <Box
            component="form"
            autoComplete="off"
            sx={{
              "& .MuiTextField-root": { mt: 1 },
            }}
          >
            <TextField
              value={name}
              label="Name"
              onChange={(event) => setName(event.target.value)}
              size="small"
              fullWidth
              required
            />
            <FormControl
              variant="outlined"
              sx={{ mt: 1 }}
              size="small"
              fullWidth
            >
              <InputLabel id="kind-label">Kind</InputLabel>
              <Select
                labelId="kind-label"
                value={kind}
                onChange={(event) => setKind(event.target.value)}
                label="Kind"
                disabled={kindFixed}
                required
                MenuProps={{
                  MenuListProps: { dense: true },
                }}
              >
                {kinds.map((kind) => (
                  <MenuItem key={kind.value} value={kind.value}>
                    {kind.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              value={path}
              label="Path"
              onChange={(event) => setPath(event.target.value)}
              size="small"
              fullWidth
              required
            />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Typography variant="subtitle2" color="error">
          {applyError}
        </Typography>
        <Button onClick={handleApply} disabled={isApplying || isLoading}>
          {props.id ? "Save" : "Create"}
        </Button>
        <Button
          onClick={handleClose}
          disabled={isApplying || isLoading}
          autoFocus
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

EditVolumeDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  id: PropTypes.string,
  onClose: PropTypes.func.isRequired,
};

export default EditVolumeDialog;
