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
    <div className="rounded-[1.75rem] border border-slate-200/70 bg-white/90 p-8 shadow-panel dark:border-slate-800 dark:bg-slate-950/80">
      <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
        Welcome back
      </p>
      <h2 className="mt-3 font-[var(--font-heading)] text-3xl font-semibold text-slate-900 dark:text-white">
        Sign in to your workspace
      </h2>
      <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
        Pick up where your report pipeline left off.
      </p>

      <form className="mt-8 space-y-5" onSubmit={onSubmit}>
        <Input
          autoComplete="email"
          error={errors.email?.message}
          label="Email"
          placeholder="you@company.com"
          register={register("email")}
          type="email"
        />
        <Input
          autoComplete="current-password"
          error={errors.password?.message}
          label="Password"
          placeholder="Enter your password"
          register={register("password")}
          type="password"
        />

        <Button className="w-full" isLoading={isLoading} type="submit">
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        New here?{" "}
        <Link
          className="font-semibold text-brand-ocean hover:text-brand-ink dark:text-brand-gold dark:hover:text-amber-200"
          href="/register"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
