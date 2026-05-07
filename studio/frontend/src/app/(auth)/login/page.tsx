"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { DEMO_LOGIN_EMAIL, DEMO_LOGIN_PASSWORD } from "@/lib/api";
import { useSession } from "@/hooks/useSession";
import { useAuthStore } from "@/store/authStore";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage(): JSX.Element {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const { isAuthenticated, isLoading } = useSession();
  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/generate");
    }
  }, [isAuthenticated, isLoading, router]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await login(values.email, values.password);
      router.push("/generate");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Unable to log in right now.",
      );
    }
  });

  return (
    <div className="p-4 sm:p-0">
      <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] backdrop-blur-sm">
        Welcome back
      </span>
      <h2 className="mt-8 text-[26px] font-semibold tracking-tight text-white">
        Sign in to Studio
      </h2>
      <p className="mt-3 text-[15px] text-[var(--text-secondary)] leading-relaxed">
        Pick up where your report pipeline left off.
      </p>

      <div className="mt-8 rounded-[var(--radius-lg)] border border-dashed border-white/10 bg-white/02 p-5 text-[13px] text-[var(--text-secondary)]">
        <p className="font-semibold text-white/60 uppercase tracking-wider text-[11px]">Demo credentials</p>
        <div className="mt-3 space-y-1 font-mono">
          <p>Email: <span className="text-white/80">{DEMO_LOGIN_EMAIL}</span></p>
          <p>Pass:  <span className="text-white/80">{DEMO_LOGIN_PASSWORD}</span></p>
        </div>
      </div>

      <form className="mt-10 space-y-6" onSubmit={onSubmit}>
        <Input
          autoComplete="email"
          error={errors.email?.message}
          label="Email Address"
          placeholder="you@company.com"
          register={register("email")}
          type="email"
        />
        <div className="space-y-2">
          <div className="flex items-center justify-between px-1">
            <label className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-tertiary)]" htmlFor="password">
              Password
            </label>
            <Link href="/forgot-password" size="sm" className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-tertiary)] hover:text-white transition-colors">
              Forgot?
            </Link>
          </div>
          <Input
            autoComplete="current-password"
            error={errors.password?.message}
            placeholder="Enter your password"
            id="password"
            register={register("password")}
            type="password"
          />
        </div>

        <Button className="w-full !rounded-full mt-2" isLoading={isLoading} type="submit" variant="primary">
          Sign in
        </Button>
      </form>

      <p className="mt-10 text-center text-[14px] text-[var(--text-secondary)]">
        New here?{" "}
        <Link
          className="font-semibold text-white hover:underline underline-offset-4"
          href="/register"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
