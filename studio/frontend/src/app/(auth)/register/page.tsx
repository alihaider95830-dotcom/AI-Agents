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
    <div className="p-4 sm:p-0">
      <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] backdrop-blur-sm">
        Start free
      </span>
      <h2 className="mt-8 text-[26px] font-semibold tracking-tight text-white">
        Create your account
      </h2>
      <p className="mt-3 text-[15px] text-[var(--text-secondary)] leading-relaxed">
        Join Studio and launch your first AI-generated report.
      </p>

      <form className="mt-10 space-y-5" onSubmit={onSubmit}>
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
          label="Email Address"
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

        <Button className="w-full !rounded-full mt-4" isLoading={isLoading} type="submit" variant="primary">
          Create account
        </Button>
      </form>

      <p className="mt-10 text-center text-[14px] text-[var(--text-secondary)]">
        Already have an account?{" "}
        <Link
          className="font-semibold text-white hover:underline underline-offset-4"
          href="/login"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
