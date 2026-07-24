import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/ai_model.dart';
import '../../providers/ai_history_provider.dart';

class FlashcardHistoryScreen extends ConsumerStatefulWidget {
  final String bookId;
  final String? bookTitle;

  const FlashcardHistoryScreen({
    required this.bookId,
    this.bookTitle,
    super.key,
  });

  @override
  ConsumerState<FlashcardHistoryScreen> createState() =>
      _FlashcardHistoryScreenState();
}

class _FlashcardHistoryScreenState extends ConsumerState<FlashcardHistoryScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(flashcardHistoryProvider.notifier).loadFlashcardSets(widget.bookId);
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final historyState = ref.watch(flashcardHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.bookTitle != null
              ? 'Flashcards - ${widget.bookTitle}'
              : 'Flashcard Sets',
        ),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref
                  .read(flashcardHistoryProvider.notifier)
                  .loadFlashcardSets(widget.bookId);
            },
          ),
        ],
      ),
      body: historyState.isLoading
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : historyState.error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Error: ${historyState.error}'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          ref
                              .read(flashcardHistoryProvider.notifier)
                              .loadFlashcardSets(widget.bookId);
                        },
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : historyState.flashcardSets.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.style_outlined,
                            size: 64,
                            color: AppTheme.textHint,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No flashcard sets yet',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Generate flashcards to see them here',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppTheme.textSecondary,
                                ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: historyState.flashcardSets.length,
                      itemBuilder: (context, index) {
                        final set = historyState.flashcardSets[index];
                        return FlashcardSetCard(
                          set: set,
                          index: index,
                        );
                      },
                    ),
    );
  }
}

class FlashcardSetCard extends ConsumerWidget {
  final FlashcardSetPublic set;
  final int index;

  const FlashcardSetCard({
    required this.set,
    required this.index,
    super.key,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final formattedDate = _formatDate(set.createdAt);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => FlashcardStudyScreen(setId: set.id),
            ),
          );
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: _getGradientColors(index),
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            set.topicName,
                            style: Theme.of(context)
                                .textTheme
                                .titleLarge
                                ?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.3),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  '${set.flashcardCount} cards',
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodySmall
                                      ?.copyWith(color: Colors.white),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                formattedDate,
                                style: Theme.of(context)
                                    .textTheme
                                    .bodySmall
                                    ?.copyWith(
                                      color: Colors.white.withOpacity(0.7),
                                    ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    Icon(
                      Icons.arrow_forward_ios,
                      color: Colors.white.withOpacity(0.7),
                      size: 20,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: 0.6,
                    minHeight: 4,
                    backgroundColor: Colors.white.withOpacity(0.2),
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Colors.white.withOpacity(0.8),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  List<Color> _getGradientColors(int index) {
    final gradients = [
      [const Color(0xFF6366F1), const Color(0xFF8B5CF6)],
      [const Color(0xFF10B981), const Color(0xFF14B8A6)],
      [const Color(0xFFF59E0B), const Color(0xFFEF4444)],
      [const Color(0xFF3B82F6), const Color(0xFF06B6D4)],
    ];
    return gradients[index % gradients.length].cast<Color>();
  }

  String _formatDate(String? dateString) {
    if (dateString == null) return 'Unknown';
    try {
      final date = DateTime.parse(dateString);
      final now = DateTime.now();
      final diff = now.difference(date);

      if (diff.inDays == 0) {
        return 'Today';
      } else if (diff.inDays == 1) {
        return 'Yesterday';
      } else if (diff.inDays < 7) {
        return '${diff.inDays} days ago';
      } else {
        return '${date.month}/${date.day}/${date.year}';
      }
    } catch (e) {
      return 'Unknown';
    }
  }
}

class FlashcardStudyScreen extends ConsumerStatefulWidget {
  final String setId;

  const FlashcardStudyScreen({
    required this.setId,
    super.key,
  });

  @override
  ConsumerState<FlashcardStudyScreen> createState() =>
      _FlashcardStudyScreenState();
}

class _FlashcardStudyScreenState extends ConsumerState<FlashcardStudyScreen>
    with SingleTickerProviderStateMixin {
  late PageController _pageController;
  late AnimationController _flipController;
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _flipController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    _flipController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final flashcardSetAsync = ref.watch(selectedFlashcardSetProvider(widget.setId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Study Flashcards'),
        elevation: 0,
      ),
      body: flashcardSetAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Go Back'),
              ),
            ],
          ),
        ),
        data: (flashcardSet) {
          if (flashcardSet == null || flashcardSet.flashcards == null || flashcardSet.flashcards!.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.style_outlined,
                      size: 64, color: AppTheme.textHint),
                  SizedBox(height: 16),
                  Text('No flashcards found'),
                ],
              ),
            );
          }

          final flashcards = flashcardSet.flashcards!;
          return Column(
            children: [
              // Progress indicator
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Card ${_currentIndex + 1}/${flashcards.length}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Text(
                          '${((_currentIndex + 1) / flashcards.length * 100).toStringAsFixed(0)}%',
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(color: AppTheme.primaryColor),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: (_currentIndex + 1) / flashcards.length,
                        minHeight: 6,
                        backgroundColor: AppTheme.textHint.withOpacity(0.2),
                        valueColor:
                            const AlwaysStoppedAnimation<Color>(
                              AppTheme.primaryColor,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
              // Flashcard carousel
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  onPageChanged: (index) {
                    setState(() {
                      _currentIndex = index;
                      _flipController.reset();
                    });
                  },
                  itemCount: flashcards.length,
                  itemBuilder: (context, index) {
                    return FlashcardWidget(
                      flashcard: flashcards[index],
                      flipController: _flipController,
                    );
                  },
                ),
              ),
              // Navigation buttons
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton.icon(
                      onPressed: _currentIndex > 0
                          ? () {
                              _pageController.previousPage(
                                duration:
                                    const Duration(milliseconds: 300),
                                curve: Curves.easeInOut,
                              );
                            }
                          : null,
                      icon: const Icon(Icons.arrow_back),
                      label: const Text('Previous'),
                    ),
                    ElevatedButton.icon(
                      onPressed:
                          _currentIndex < flashcards.length - 1
                              ? () {
                                  _pageController.nextPage(
                                    duration:
                                        const Duration(milliseconds: 300),
                                    curve: Curves.easeInOut,
                                  );
                                }
                              : null,
                      icon: const Icon(Icons.arrow_forward),
                      label: const Text('Next'),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class FlashcardWidget extends ConsumerStatefulWidget {
  final FlashcardPublic flashcard;
  final AnimationController flipController;

  const FlashcardWidget({
    required this.flashcard,
    required this.flipController,
    super.key,
  });

  @override
  ConsumerState<FlashcardWidget> createState() => _FlashcardWidgetState();
}

class _FlashcardWidgetState extends ConsumerState<FlashcardWidget> {
  bool _isFlipped = false;

  void _toggleFlip() {
    setState(() {
      _isFlipped = !_isFlipped;
      if (_isFlipped) {
        widget.flipController.forward();
      } else {
        widget.flipController.reverse();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: GestureDetector(
        onTap: _toggleFlip,
        child: AnimatedBuilder(
          animation: widget.flipController,
          builder: (context, child) {
            final angle = widget.flipController.value * 3.14159;
            final transform = Matrix4.identity();
            transform.setEntry(3, 2, 0.001);
            transform.rotateY(angle);

            return Transform(
              alignment: Alignment.center,
              transform: transform,
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primaryColor.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Card(
                  elevation: 8,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(20),
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: _isFlipped
                            ? [
                                const Color(0xFF10B981),
                                const Color(0xFF14B8A6),
                              ]
                            : [
                                AppTheme.primaryColor,
                                AppTheme.secondaryColor,
                              ],
                      ),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _isFlipped ? 'Answer' : 'Question',
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(
                                  color: Colors.white.withOpacity(0.7),
                                  letterSpacing: 1.5,
                                ),
                          ),
                          const SizedBox(height: 16),
                          Expanded(
                            child: SingleChildScrollView(
                              child: Text(
                                _isFlipped
                                    ? widget.flashcard.back
                                    : widget.flashcard.front,
                                textAlign: TextAlign.center,
                                style: Theme.of(context)
                                    .textTheme
                                    .headlineSmall
                                    ?.copyWith(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w600,
                                      height: 1.5,
                                    ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Tap to reveal',
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(
                                  color: Colors.white.withOpacity(0.5),
                                ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
