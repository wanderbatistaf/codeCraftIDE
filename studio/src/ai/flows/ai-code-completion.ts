'use server';

/**
 * @fileOverview AI code completion flow.
 *
 * - aiCodeCompletion - A function that handles the code completion process.
 * - AICodeCompletionInput - The input type for the aiCodeCompletion function.
 * - AICodeCompletionOutput - The return type for the aiCodeCompletion function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AICodeCompletionInputSchema = z.object({
  codePrefix: z
    .string()
    .describe('The code prefix that the user has already typed.'),
  language: z.string().describe('The programming language of the code.'),
});
export type AICodeCompletionInput = z.infer<typeof AICodeCompletionInputSchema>;

const AICodeCompletionOutputSchema = z.object({
  completion: z.string().describe('The suggested code completion.'),
});
export type AICodeCompletionOutput = z.infer<typeof AICodeCompletionOutputSchema>;

export async function aiCodeCompletion(input: AICodeCompletionInput): Promise<AICodeCompletionOutput> {
  return aiCodeCompletionFlow(input);
}

const codeCompletionPrompt = ai.definePrompt({
  name: 'codeCompletionPrompt',
  input: {schema: AICodeCompletionInputSchema},
  output: {schema: AICodeCompletionOutputSchema},
  prompt: `You are an AI code completion assistant.  Given the following code prefix and programming language, suggest a code completion.

Language: {{{language}}}
Code Prefix:
{{codePrefix}}`,
});

const aiCodeCompletionFlow = ai.defineFlow(
  {
    name: 'aiCodeCompletionFlow',
    inputSchema: AICodeCompletionInputSchema,
    outputSchema: AICodeCompletionOutputSchema,
  },
  async input => {
    const {output} = await codeCompletionPrompt(input);
    return output!;
  }
);
