import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "sonner";

import LoginPage from "@/app/(auth)/login/page";
import RegisterPage from "@/app/(auth)/register/page";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
}));

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
  },
}));

jest.mock("@/lib/api", () => ({
  AUTH_TOKEN_STORAGE_KEY: "ai-report-token",
  redirectToLogin: jest.fn(),
  authApi: {
    login: jest.fn(),
    register: jest.fn(),
    me: jest.fn(),
  },
}));

const mockedAuthApi = authApi as jest.Mocked<typeof authApi>;
const mockedToast = toast as jest.Mocked<typeof toast>;

const mockUser = {
  id: "user-1",
  email: "ali@example.com",
  full_name: "Ali Haider",
  tier: "free" as const,
  credits: 12,
};

describe("auth pages", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    });
  });

  it("test_login_form_renders", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i }),
    ).toBeInTheDocument();
  });

  it("test_login_validation", async () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByText("Please enter a valid email address."),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Password must be at least 8 characters."),
    ).toBeInTheDocument();
  });

  it("test_login_success", async () => {
    mockedAuthApi.login.mockResolvedValue({ access_token: "token-123" });
    mockedAuthApi.me.mockResolvedValue(mockUser);

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "ali@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/generate");
    });
  });

  it("test_login_error", async () => {
    mockedAuthApi.login.mockRejectedValue(new Error("Invalid credentials"));

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "ali@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith("Invalid credentials");
    });
  });

  it("test_register_password_mismatch", async () => {
    render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText(/full name/i), {
      target: { value: "Ali Haider" },
    });
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "ali@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "password321" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(
      await screen.findByText("Passwords must match."),
    ).toBeInTheDocument();
  });
});
