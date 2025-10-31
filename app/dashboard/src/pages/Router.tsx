import { createHashRouter, Navigate, Outlet } from "react-router-dom";
import { fetch, $fetch } from "../service/http";
import { getAuthToken, setAuthToken } from "../utils/authStorage";
import { Dashboard } from "./Dashboard";
import { Login } from "./Login";
import { Register } from "./Register";
import { UserCenter } from "./UserCenter";
import UserOrders from "./UserOrders";
import UserConfig from "./UserConfig";
import UserPayment from "./UserPayment";
import { AuthProvider } from "../contexts/AuthContext";

const Root = () => (
  <AuthProvider>
    <Outlet />
  </AuthProvider>
);

const fetchAdminLoader = async () => {
  try {
    return await fetch("/admin", {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
  } catch (error) {
    throw new Response("", {
      status: 401,
      statusText: "Unauthorized",
    });
  }
};

const requireAuth = async () => {
  const token = getAuthToken();
  // 若无 access_token，尝试通过 refresh_token 刷新
  if (!token) {
    const rt = localStorage.getItem('refresh_token');
    if (rt) {
      try {
        const resp = await $fetch<{ access_token?: string }>("/token/refresh", {
          method: "POST",
          body: { refresh_token: rt },
          headers: { "Content-Type": "application/json" },
        });
        if (resp?.access_token) {
          setAuthToken(resp.access_token);
          return null;
        }
      } catch (e) {
        // fallthrough to redirect
      }
    }
    throw new Response("", {
      status: 401,
      statusText: "Unauthorized",
    });
  }

  // 若存在 access_token，再进行一次轻量校验，避免组件挂载后再失败导致请求被取消
  try {
    await fetch("/user/me", {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return null;
  } catch (error) {
    // 校验失败时尝试刷新一次
    const rt = localStorage.getItem('refresh_token');
    if (rt) {
      try {
        const resp = await $fetch<{ access_token?: string }>("/token/refresh", {
          method: "POST",
          body: { refresh_token: rt },
          headers: { "Content-Type": "application/json" },
        });
        if (resp?.access_token) {
          setAuthToken(resp.access_token);
          return null;
        }
      } catch (e) {
        // fallthrough
      }
    }
    throw new Response("", {
      status: 401,
      statusText: "Unauthorized",
    });
  }
};

export const router = createHashRouter([
  {
    element: <Root />,
    errorElement: <Navigate to="/login" />,
    children: [
      {
        path: "/",
        element: <Navigate to="/user" />,
      },
      {
        path: "/admin",
        element: <Dashboard />,
        errorElement: <Navigate to="/login" />,
        loader: fetchAdminLoader,
      },
      {
        path: "/login",
        element: <Login />,
      },
      {
        path: "/register",
        element: <Register />,
      },
      {
        path: "/user",
        element: <UserCenter />,
        loader: requireAuth,
        errorElement: <Navigate to="/login" />,
      },
      {
        path: "/user/orders",
        element: <UserOrders />,
        loader: requireAuth,
        errorElement: <Navigate to="/login" />,
      },
      {
        path: "/user/config",
        element: <UserConfig />,
        loader: requireAuth,
        errorElement: <Navigate to="/login" />,
      },
      {
        path: "/user/payment",
        element: <UserPayment />,
        loader: requireAuth,
        errorElement: <Navigate to="/login" />,
      },
    ],
  },
]);
