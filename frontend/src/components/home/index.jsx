import React from "react";
import { styled } from "@mui/material/styles";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import useMediaQuery from "@mui/material/useMediaQuery";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import StorageIcon from "@mui/icons-material/Storage";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SettingsIcon from "@mui/icons-material/Settings";
import Fade from "@mui/material/Fade";
import Skeleton from "@mui/material/Skeleton";
import PersonIcon from "@mui/icons-material/Person";
import LinearProgress from "@mui/material/LinearProgress";

import { ajax } from "../../utils/generics";
import { UserContext } from "../../utils/contexts";

const AppButton = styled(Button)(() => ({
  width: 180,
  height: 100,
  transition: "transform .2s",
  ":hover": {
    transform: "scale(1.3)",
  },
  animation: "fadeIn 0.7s ease",
}));

const Home = () => {
  const navigate = useNavigate();
  const wideView = useMediaQuery("(min-width:600px)");
  const [self, setSelf] = React.useState(null);
  const userContext = React.useContext(UserContext);
  const apps = React.useMemo(
    () => [
      {
        name: "File Explorer",
        url: "/drive/my-drive",
        icon: <StorageIcon />,
        needsAdmin: false,
      },
      {
        name: "Media Player",
        url: "/drive/media-player",
        icon: <PlayArrowIcon />,
        needsAdmin: false,
      },
      {
        name: "Settings",
        url: "/drive/settings/users",
        icon: <SettingsIcon />,
        needsAdmin: true,
      },
      {
        name: "Profile",
        url: "/drive/profile",
        icon: <PersonIcon />,
        needsAdmin: false,
      },
    ],
    []
  );
  const repoUrl = "https://gitlab.com/kingkingyyk/RPiDrive";
  const poweredBy = React.useMemo(
    () => [
      {
        name: "Django",
        url: "https://www.djangoproject.com/",
      },
      {
        name: "React",
        url: "https://react.dev/",
      },
      {
        name: "MUI",
        url: "https://mui.com/",
      },
      {
        name: "MRT",
        url: "https://www.material-react-table.com/",
      },
    ],
    []
  );

  React.useEffect(() => {
    document.title = "RPi Drive";
    if (!userContext) return;
    setSelf(userContext);
  }, [userContext]);

  const logout = () => {
    ajax
      .post("/drive/ui-api/users/logout")
      .then(() => {
        navigate("/drive/login");
      })
      .catch((reason) => console.error(reason));
  };

  if (!userContext) {
    return (
      <Box>
        <Box className="background" />
        <LinearProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box className="background" />
      <Box sx={{ width: "100%", textAlign: "right", p: 1 }}>
        <Button size="small" color="warning" onClick={logout}>
          Logout
        </Button>
      </Box>
      <Box sx={{ height: wideView ? "10vh" : "0" }} />
      <Fade in>
        <Typography
          variant="h2"
          color="primary"
          sx={{ width: "100%", textAlign: "center", p: 1 }}
        >
          RPi Drive
        </Typography>
      </Fade>
      <Box sx={{ height: wideView ? "10vh" : "15px" }} />
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={{ xs: 1, sm: 2, md: 4 }}
        divider={<Divider orientation="vertical" flexItem />}
        alignItems="center"
        justifyContent="center"
        sx={{ pl: 3, pr: 3 }}
      >
        {!self || !self.id ? (
          <Skeleton width="60vw" height="100px" />
        ) : (
          apps
            .filter((app) => self.is_superuser || !app.needsAdmin)
            .map((app) => (
              <AppButton
                variant="outlined"
                component={RouterLink}
                to={app.url}
                key={app.name}
                startIcon={app.icon}
              >
                {app.name}
              </AppButton>
            ))
        )}
      </Stack>
      <Box className="footer">
        <Typography color="primary" variant="subtitle2">
          Source available on{" "}
          <Box
            component={RouterLink}
            to={repoUrl}
            target="_blank"
            rel="noopener noreferrer"
            sx={{ color: "inherit" }}
          >
            GitLab
          </Box>
          . Powered by{" "}
          {poweredBy.map((comp, idx) => (
            <React.Fragment key={comp.name}>
              <Box
                component={RouterLink}
                to={comp.url}
                target="_blank"
                rel="noopener noreferrer"
                sx={{ color: "inherit" }}
                key={comp.name}
              >
                {comp.name}
              </Box>
              {idx < poweredBy.length - 1 ? ", " : "."}
            </React.Fragment>
          ))}
        </Typography>
      </Box>
    </Box>
  );
};

export default Home;
