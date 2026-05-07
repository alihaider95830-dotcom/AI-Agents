"use client";

import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { Plus } from "lucide-react";

import { cn } from "@/lib/utils";

const Accordion = AccordionPrimitive.Root;

const AccordionItem = ({
  className,
  ...props
}: AccordionPrimitive.AccordionItemProps): JSX.Element => (
  <AccordionPrimitive.Item
    className={cn("border-b border-white/05 last:border-0", className)}
    {...props}
  />
);
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = ({
  className,
  children,
  ...props
}: AccordionPrimitive.AccordionTriggerProps): JSX.Element => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      className={cn(
        "flex flex-1 items-center justify-between py-6 text-left text-[15px] font-medium text-[var(--text-primary)] transition-all hover:text-white group [&[data-state=open]>svg]:rotate-45",
        className,
      )}
      {...props}
    >
      {children}
      <Plus className="h-4 w-4 shrink-0 text-[var(--text-tertiary)] transition-transform duration-300 group-hover:text-white" />
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
);
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = ({
  className,
  children,
  ...props
}: AccordionPrimitive.AccordionContentProps): JSX.Element => (
  <AccordionPrimitive.Content
    className={cn(
      "overflow-hidden text-[14px] text-[var(--text-secondary)] data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down",
      className,
    )}
    {...props}
  >
    <div className="pb-6 pt-0 leading-relaxed max-w-2xl">{children}</div>
  </AccordionPrimitive.Content>
);
AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
