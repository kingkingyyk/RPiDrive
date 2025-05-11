import React from "react";
import PropTypes from "prop-types";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

const DeleteDialog = (props) => {
  const [validText, setValidText] = React.useState(
    props.validateText ? "" : props.validateText
  );

  return (
    <Dialog open onClose={props.onCancel}>
      <DialogTitle>{props.title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{props.message}</DialogContentText>
        {props.validateText && (
          <TextField
            sx={{ mt: 1 }}
            value={validText}
            onChange={(event) => setValidText(event.target.value)}
            size="small"
            label={`Fill in "${props.validateText}" to proceed`}
            error={validText !== props.validateText}
            fullWidth
            required
          />
        )}
      </DialogContent>
      <DialogActions>
        <Typography variant="subtitle2" color="error">
          {props.errorMsg}
        </Typography>
        <Button
          onClick={props.onApply}
          disabled={props.loading || validText !== props.validateText}
          color="error"
        >
          Delete
        </Button>
        <Button onClick={props.onCancel} disabled={props.loading} autoFocus>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

DeleteDialog.propTypes = {
  title: PropTypes.string.isRequired,
  message: PropTypes.string.isRequired,
  validateText: PropTypes.string,
  onApply: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  loading: PropTypes.func.isRequired,
  errorMsg: PropTypes.string,
};

export default DeleteDialog;
