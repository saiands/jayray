from django.db import models

# --- Reusable Components (Checklist/Dropdown Options) ---

class PromptRule(models.Model):
    """
    Stores non-negotiable constraints, used in the '# RULES' section.
    These act as checklist items for an admin to select when building a template.
    """
    name = models.CharField(max_length=255, unique=True, help_text="A short title for this rule (e.g., 'Exclude popular options').")
    text = models.TextField(help_text="The actual text of the rule to be inserted into the prompt.")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Rule"
        verbose_name_plural = "Rules (Non-Negotiables)"

    def __str__(self):
        return self.name

class PromptStep(models.Model):
    """
    Stores individual steps for internal processing, used in the '## REASONING' section.
    These define the focus and validation steps (e.g., 'Cross-check against official listings').
    """
    name = models.CharField(max_length=255, unique=True, help_text="A short title for this reasoning step.")
    text = models.TextField(help_text="The actual reasoning step to be inserted into the prompt.")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Reasoning Step"
        verbose_name_plural = "Reasoning Steps (Internal Logic)"

    def __str__(self):
        return self.name

# --- NEW MODEL FOR DYNAMIC FIELDS ---

class DynamicPromptField(models.Model):
    """
    Stores custom, dynamic key-value pairs that can be added to any PromptTemplate.
    e.g., Label: "Target Platform", Value: "YouTube Shorts"
    """
    template = models.ForeignKey(
        'PromptTemplate', 
        on_delete=models.CASCADE, 
        related_name='dynamic_fields',
        help_text="The prompt template this custom field belongs to."
    )
    label_key = models.CharField(max_length=100, help_text="The label for the field (e.g., 'Target Platform').")
    field_value = models.TextField(help_text="The value for this field (e.g., 'Short video format').")
    order = models.PositiveSmallIntegerField(default=0, help_text="The order in which to display this field.")

    class Meta:
        verbose_name = "Dynamic Parameter"
        verbose_name_plural = "Dynamic Parameters (Fixed Visual Parameters)"
        ordering = ['order', 'label_key']

    def __str__(self):
        return f"{self.label_key}: {self.field_value[:30]}"


# --- The Main Prompt Template ---

class PromptTemplate(models.Model):
    """
    The main model storing the fully structured template based on your best-practice pattern:
    Role, Task, Context, Reasoning, Rules, Output Format, Stop Conditions.
    """
    # Metadata
    name = models.CharField(max_length=255, unique=True, help_text="A descriptive name for this template (e.g., 'YouTube Script Breakdown').")
    description = models.TextField(blank=True, help_text="Internal notes about when to use this template.")

    # Core Text Sections (Text Input / Text Area)
    role_text = models.TextField(help_text="The 'You are...' definition for the # ROLE section.")
    task_text = models.TextField(help_text="The core objective for the ## TASK section.")
    context_text = models.TextField(blank=True, null=True, help_text="Any grounding information for the ## CONTEXT section (optional).")
    stop_conditions = models.TextField(blank=True, null=True, help_text="The criteria for the ## STOP CONDITIONS section (e.g., 'Task is complete when...').")
    output_format = models.TextField(blank=True, null=True, help_text="The required structure for the ## OUTPUT FORMAT section (e.g., 'Return results as a JSON object...').")

    # Reusable Component Sections (Checklist / Many-to-Many Fields)
    rules = models.ManyToManyField(PromptRule, blank=True, related_name='templates', 
                                   help_text="Select specific rules for the # RULES section.")
    reasoning_steps = models.ManyToManyField(PromptStep, blank=True, related_name='templates', 
                                            help_text="Select internal reasoning/validation steps for the ## REASONING section.")

    class Meta:
        verbose_name = "Prompt Template"
        verbose_name_plural = "Prompt Templates (The Prompt House)"

    def __str__(self):
        return self.name

    def assemble_prompt(self):
        """
        Assembles the final, focused prompt string using your required Markdown structure,
        including the newly added dynamic fields.
        """
        
        prompt_parts = [
            "# ROLE",
            f"You are {self.role_text.strip()}.",
        ]
        
        prompt_parts.append("\n## TASK")
        prompt_parts.append(self.task_text.strip())
        
        # 3. Context & Dynamic Fields (Fixed Visual Parameters)
        if self.context_text or self.dynamic_fields.exists():
            prompt_parts.append("\n## CONTEXT")
            if self.context_text:
                prompt_parts.append(self.context_text.strip())
                
            if self.dynamic_fields.exists():
                prompt_parts.append("\nFixed Parameters (Apply to every image):")
                # Using order to sort dynamic fields
                for field in self.dynamic_fields.all().order_by('order'): 
                    prompt_parts.append(f"{field.label_key}: {field.field_value.strip()}")

        # 4. Reasoning Steps (Checklist of steps)
        if self.reasoning_steps.exists():
            prompt_parts.append("\n## REASONING")
            steps = [step.text.strip() for step in self.reasoning_steps.all()]
            for i, step in enumerate(steps, 1):
                prompt_parts.append(f"{i}. {step}")
        
        # 5. Rules (Non-negotiables)
        if self.rules.exists():
            prompt_parts.append("\n# RULES")
            for rule in self.rules.all():
                prompt_parts.append(f"- {rule.text.strip()}")
        
        # 6. Output Format
        if self.output_format:
            prompt_parts.append("\n## OUTPUT FORMAT")
            prompt_parts.append(self.output_format.strip())
            
        # 7. Stop Conditions
        if self.stop_conditions:
            prompt_parts.append("\n## STOP CONDITIONS")
            prompt_parts.append(self.stop_conditions.strip())

        return "\n".join(prompt_parts)  