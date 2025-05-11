import React from "react";
import ListSubheader from "@mui/material/ListSubheader";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Avatar from "@mui/material/Avatar";
import DeveloperBoardIcon from "@mui/icons-material/DeveloperBoard";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import AppsIcon from "@mui/icons-material/Apps";
import StorageIcon from "@mui/icons-material/Storage";
import MemoryIcon from "@mui/icons-material/Memory";
import Skeleton from "@mui/material/Skeleton";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import Box from "@mui/material/Box";

import prettyBytes from "pretty-bytes";
import { ajax } from "../../../utils/generics";
import { blue, purple, red, orange } from "@mui/material/colors";

const System = () => {
  const [cpuInfo, setCpuInfo] = React.useState([
    {
      name: "Model",
      value: null,
    },
    {
      name: "Core(s)",
      value: null,
    },
    {
      name: "Frequency",
      value: null,
    },
    {
      name: "Usage",
      value: null,
    },
  ]);
  const [memInfo, setMemInfo] = React.useState([
    {
      name: "Total",
      value: null,
    },
    {
      name: "Used",
      value: null,
    },
  ]);
  const [diskInfo, setDiskInfo] = React.useState([]);
  const [envInfo, setEnvInfo] = React.useState([
    {
      name: "OS",
      value: null,
    },
    {
      name: "Arch",
      value: null,
    },
    {
      name: "Python",
      value: null,
    },
  ]);

  const loadData = () => {
    ajax
      .get("/drive/ui-api/system/details")
      .then((response) => {
        const cpu = response.data.cpu;
        let nCpuInfo = [...cpuInfo];
        nCpuInfo[0].value = cpu.model;
        nCpuInfo[1].value = cpu.cores;
        nCpuInfo[2].value = `${cpu.frequency} MHz`;
        nCpuInfo[3].value = `${cpu.usage} %`;
        setCpuInfo(nCpuInfo);

        const mem = response.data.memory;
        let nMemInfo = [...memInfo];
        nMemInfo[0].value = prettyBytes(mem.total);
        nMemInfo[1].value = prettyBytes(mem.used);
        setMemInfo(nMemInfo);

        const disks = response.data.disks;
        let temp = [];
        for (let disk of disks) {
          temp.push({
            name: disk.name,
            value: `${prettyBytes(disk.used)} (${
              disk.percent
            }%) used of ${prettyBytes(disk.total)}`,
          });
        }
        setDiskInfo(temp);

        const environ = response.data.environment;
        let nEnvInfo = [...envInfo];
        nEnvInfo[0].value = environ.os;
        nEnvInfo[1].value = environ.arch;
        nEnvInfo[2].value = environ.python;
        setEnvInfo(nEnvInfo);
      })
      .catch((reason) => console.error(reason));
  };

  React.useEffect(() => {
    document.title = "System - RPi Drive";
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" color="primary">
        System
      </Typography>
      <Divider sx={{ mt: 1 }} />
      <List
        component="nav"
        subheader={<ListSubheader component="div">CPU</ListSubheader>}
        dense
      >
        {cpuInfo.length === 0 && (
          <ListItem>
            <Skeleton width={100} />
          </ListItem>
        )}
        {cpuInfo.map((info) => (
          <ListItem key={info.name}>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: red[500] }}>
                <DeveloperBoardIcon />
              </Avatar>
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
        subheader={<ListSubheader component="div">Memory</ListSubheader>}
        dense
      >
        {memInfo.length === 0 && (
          <ListItem>
            <Skeleton width={100} />
          </ListItem>
        )}
        {memInfo.map((info) => (
          <ListItem key={info.name}>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: blue[500] }}>
                <MemoryIcon />
              </Avatar>
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
        subheader={<ListSubheader component="div">Disks</ListSubheader>}
        dense
      >
        {diskInfo.length === 0 && (
          <ListItem>
            <ListItemAvatar>
              <Avatar>
                <Skeleton variant="circular" width={40} height={40} />
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={<Skeleton width={100} />}
              secondary={<Skeleton width={100} />}
            />
          </ListItem>
        )}
        {diskInfo.map((info) => (
          <ListItem key={info.name}>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: purple[500] }}>
                <StorageIcon />
              </Avatar>
            </ListItemAvatar>
            <ListItemText primary={info.name} secondary={info.value} />
          </ListItem>
        ))}
      </List>
      <List
        component="nav"
        subheader={<ListSubheader component="div">Environment</ListSubheader>}
        dense
      >
        {envInfo.length === 0 && (
          <ListItem>
            <Skeleton width={100} />
          </ListItem>
        )}
        {envInfo.map((info) => (
          <ListItem key={info.name}>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: orange[500] }}>
                <AppsIcon />
              </Avatar>
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

export default System;
