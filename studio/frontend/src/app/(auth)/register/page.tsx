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

const registerSchema = z
  .object({
    full_name: z.string().min(2, "Full name must be at least 2 characters."),
    email: z.string().email("Please enter a valid email address."),
    password: z.string().min(8, "Password must be at least 8 characters."),
    confirm_password: z
      .string()
      .min(8, "Please confirm your password with at least 8 characters."),
  })
  .refine((values) => values.password === values.confirm_password, {
    message: "Passwords must match.",
    path: ["confirm_password"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage(): JSX.Element {
  const router = useRouter();
  const registerAccount = useAuthStore((state) => state.register);
  const { isAuthenticated, isLoading } = useSession();
  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/generate");
    }
  }, [isAuthenticated, isLoading, router]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await registerAccount(values.email, values.password, values.full_name);
      router.push("/generate");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Unable to create your account right now.",
      );
    }
  });

  return (
    <div className="rounded-[1.75rem] border border-slate-200/70 bg-white/90 p-8 shadow-panel dark:border-slate-800 dark:bg-slate-950/80">
      <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
        Start free
      </p>
      <h2 className="mt-3 font-[var(--font-heading)] text-3xl font-semibold text-slate-900 dark:text-white">
        Create your account
      </h2>
      <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
        Join the workspace and launch your first AI-generated report.
      </p>

      <form className="mt-8 space-y-5" onSubmit={onSubmit}>
        <Input
          autoComplete="name"
          error={errors.full_name?.message}
          label="Full name"
          placeholder="Ali Haider"
          register={register("full_name")}
        />
        <Input
          autoComplete="email"
          error={errors.email?.message}
          label="Email"
          placeholder="you@company.com"
          register={register("email")}
          type="email"
        />
        <Input
          autoComplete="new-password"
          error={errors.password?.message}
          label="Password"
          placeholder="Create a password"
          register={register("password")}
          type="password"
        />
        <Input
          autoComplete="new-password"
          error={errors.confirm_password?.message}
          label="Confirm password"
          placeholder="Re-enter your password"
          register={register("confirm_password")}
          type="password"
        />

        <Button className="w-full" isLoading={isLoading} type="submit">
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        Already have an account?{" "}
        <Link
          className="font-semibold text-brand-ocean hover:text-brand-ink dark:text-brand-gold dark:hover:text-amber-200"
          href="/login"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
