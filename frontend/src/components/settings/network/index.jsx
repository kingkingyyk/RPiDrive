import React from "react";
import ListSubheader from "@mui/material/ListSubheader";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import ListItemText from "@mui/material/ListItemText";
import Skeleton from "@mui/material/Skeleton";
import Avatar from "@mui/material/Avatar";
import DownloadIcon from "@mui/icons-material/Download";
import UploadIcon from "@mui/icons-material/Upload";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import Box from "@mui/material/Box";

import prettyBytes from "pretty-bytes";
import { ajax } from "../../../utils/generics";
import { amber, blueGrey } from "@mui/material/colors";

const Network = () => {
  const [speed, setSpeed] = React.useState([
    { name: "Download", value: null, icon: <DownloadIcon /> },
    { name: "Upload", value: null, icon: <UploadIcon /> },
  ]);
  const [total, setTotal] = React.useState([
    { name: "Downloads", value: null, icon: <DownloadIcon /> },
    { name: "Uploads", value: null, icon: <UploadIcon /> },
  ]);

  const loadData = () => {
    ajax
      .get("/drive/ui-api/system/network")
      .then((response) => {
        const nSpeed = [...speed];
        nSpeed[0].value = `${prettyBytes(response.data.download_speed)}/s`;
        nSpeed[1].value = `${prettyBytes(response.data.upload_speed)}/s`;
        setSpeed(nSpeed);

        const lTotal = [...total];
        lTotal[0].value = prettyBytes(response.data.downloads);
        lTotal[1].value = prettyBytes(response.data.uploads);
        setTotal(lTotal);
      })
      .catch((reason) => console.error(reason));
  };

  React.useEffect(() => {
    document.title = "Network - RPi Drive";
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" color="primary">
        Network
      </Typography>
      <Divider sx={{ mt: 1 }} />
      <List
        component="nav"
        subheader={<ListSubheader component="div">Speed</ListSubheader>}
        dense
      >
        {speed.map((info) => (
          <ListItem key={info.name}>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: blueGrey[500] }}>{info.icon}</Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={info.name}
              secondary={
                info.value === null ? <Skeleton width={100} /> : info.value
              }
            />
          </ListItem>
        ))}
      </List>
      <List
        component="nav"
        subheader={<ListSubheader component="div">Total</ListSubheader>}
        dense
      >
        {total.map((info) => (
          <ListItem key={info.name}>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: amber[500] }}>{info.icon}</Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={info.name}
              secondary={
                info.value === null ? <Skeleton width={100} /> : info.value
              }
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default Network;
