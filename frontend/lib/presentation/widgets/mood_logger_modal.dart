import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/mood_log_model.dart';
import '../providers/mood_provider.dart';

class MoodLoggerModal extends ConsumerWidget {
  const MoodLoggerModal({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final moodState = ref.watch(moodProvider);
    final theme = Theme.of(context);

    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
      ),
      elevation: 8,
      child: Container(
        padding: const EdgeInsets.all(20),
        constraints: const BoxConstraints(maxWidth: 420),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.colorScheme.surface,
              theme.colorScheme.surface.withOpacity(0.9),
            ],
          ),
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
            // Title with emoji and decorative elements
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer.withOpacity(0.3),
                shape: BoxShape.circle,
              ),
              child: const Text(
                '💭',
                style: TextStyle(fontSize: 32),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'How are you feeling today?',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
                height: 1.2,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 6),
            Text(
              'Help us personalize your learning journey',
              style: TextStyle(
                fontSize: 12,
                color: theme.colorScheme.onSurface.withOpacity(0.6),
                fontWeight: FontWeight.w400,
                height: 1.3,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 18),

            // Error message with improved styling
            if (moodState.error != null)
              Container(
                padding: const EdgeInsets.all(10),
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Colors.red[200]!,
                    width: 1,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: Colors.red[700], size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        moodState.error!,
                        style: TextStyle(
                          color: Colors.red[900],
                          fontSize: 13,
                        ),
                        textAlign: TextAlign.left,
                      ),
                    ),
                  ],
                ),
              ),

            // Mood grid (2 rows of 4)
            _buildMoodGrid(context, ref, moodState.isLoading, theme),

            const SizedBox(height: 16),

            // Skip button with improved styling
            TextButton.icon(
              onPressed: moodState.isLoading
                  ? null
                  : () {
                      ref.read(moodProvider.notifier).hideModal();
                      Navigator.of(context).pop();
                    },
              icon: Icon(
                Icons.close,
                size: 18,
                color: moodState.isLoading 
                    ? Colors.grey 
                    : theme.colorScheme.onSurface.withOpacity(0.5),
              ),
              label: Text(
                'Skip for now',
                style: TextStyle(
                  color: moodState.isLoading 
                      ? Colors.grey 
                      : theme.colorScheme.onSurface.withOpacity(0.5),
                  fontSize: 14,
                ),
              ),
            ),
          ],
        ),
        ),
      ),
    );
  }

  Widget _buildMoodGrid(BuildContext context, WidgetRef ref, bool isLoading, ThemeData theme) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 0.9,
      ),
      itemCount: MoodEmotion.allMoods.length,
      itemBuilder: (context, index) {
        final mood = MoodEmotion.allMoods[index];
        return _buildMoodButton(context, ref, mood, isLoading, theme);
      },
    );
  }

  Widget _buildMoodButton(
    BuildContext context,
    WidgetRef ref,
    MoodEmotion mood,
    bool isLoading,
    ThemeData theme,
  ) {
    // Define mood-specific colors
    Color getMoodColor(String label) {
      switch (label) {
        case 'confused':
          return Colors.amber.shade100;
        case 'frustrated':
          return Colors.red.shade100;
        case 'stressed':
          return Colors.orange.shade100;
        case 'motivated':
          return Colors.green.shade100;
        case 'engaged':
          return Colors.blue.shade100;
        case 'bored':
          return Colors.grey.shade200;
        case 'neutral':
          return Colors.blueGrey.shade100;
        case 'confident':
          return Colors.purple.shade100;
        default:
          return Colors.grey.shade100;
      }
    }

    Color getMoodBorderColor(String label) {
      switch (label) {
        case 'confused':
          return Colors.amber.shade300;
        case 'frustrated':
          return Colors.red.shade300;
        case 'stressed':
          return Colors.orange.shade300;
        case 'motivated':
          return Colors.green.shade300;
        case 'engaged':
          return Colors.blue.shade300;
        case 'bored':
          return Colors.grey.shade400;
        case 'neutral':
          return Colors.blueGrey.shade300;
        case 'confident':
          return Colors.purple.shade300;
        default:
          return Colors.grey.shade300;
      }
    }

    final backgroundColor = isLoading ? Colors.grey[200] : getMoodColor(mood.label);
    final borderColor = isLoading ? Colors.grey[300]! : getMoodBorderColor(mood.label);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: isLoading
            ? null
            : () async {
                final success =
                    await ref.read(moodProvider.notifier).logMood(mood.label);
                if (success && context.mounted) {
                  // Show brief confirmation
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Row(
                        children: [
                          Text(mood.emoji, style: const TextStyle(fontSize: 20)),
                          const SizedBox(width: 8),
                          Text('Mood logged: ${mood.description}'),
                        ],
                      ),
                      duration: const Duration(milliseconds: 1500),
                      behavior: SnackBarBehavior.floating,
                      backgroundColor: theme.colorScheme.primary,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  );
                  // Close modal
                  Navigator.of(context).pop();
                }
              },
        borderRadius: BorderRadius.circular(12),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: borderColor,
              width: 1.5,
            ),
            boxShadow: isLoading
                ? []
                : [
                    BoxShadow(
                      color: borderColor.withOpacity(0.3),
                      blurRadius: 4,
                      offset: const Offset(0, 2),
                    ),
                  ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(6),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  mood.emoji,
                  style: const TextStyle(fontSize: 24),
                ),
                const SizedBox(height: 4),
                Flexible(
                  child: Text(
                    mood.description,
                    style: TextStyle(
                      fontSize: 9,
                      color: isLoading ? Colors.grey : Colors.grey[850],
                      fontWeight: FontWeight.w600,
                      height: 1.1,
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
