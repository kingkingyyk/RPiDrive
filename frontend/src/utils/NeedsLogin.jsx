import React from "react";
import { Outlet, useNavigate } from "react-router-dom";

import { ajax } from "./generics";
import { UserContext } from "./contexts";

const NeedsLogin = () => {
  const navigate = useNavigate();
  const [contextV, setContextV] = React.useState(null);

  const check = () => {
    ajax.get("/drive/ui-api/users/self").then((response) => {
      if (response.headers["content-type"] === "application/json") {
        setContextV(response.data);
      } else {
        navigate({
          pathname: "/drive/login",
          search: "?next=" + window.location.pathname,
        });
      }
    }).catch(() => {});
  };

  React.useEffect(() => {
    check();
    const interval = setInterval(() => check(), 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <UserContext.Provider value={contextV}>
      <Outlet />
    </UserContext.Provider>
  );
};

export default NeedsLogin;
