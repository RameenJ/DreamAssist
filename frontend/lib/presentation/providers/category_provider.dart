import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/category_model.dart';
import '../../data/services/category_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'category_provider.g.dart';

/// Category state
class CategoryState {
  final List<CategoryModel> categories;
  final bool isLoading;
  final String? error;

  const CategoryState({
    this.categories = const [],
    this.isLoading = false,
    this.error,
  });

  CategoryState copyWith({
    List<CategoryModel>? categories,
    bool? isLoading,
    String? error,
  }) {
    return CategoryState(
      categories: categories ?? this.categories,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Category state notifier
@riverpod
class Category extends _$Category {
  @override
  CategoryState build() {
    return const CategoryState();
  }

  CategoryApiService get _categoryService => ref.watch(categoryApiServiceProvider);

  /// Fetch all categories
  Future<void> fetchCategories() async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _categoryService.getCategories();
    result.when(
      success: (categories) {
        state = state.copyWith(categories: categories, isLoading: false);
      },
      failure: (message) {
        state = state.copyWith(isLoading: false, error: message);
      },
    );
  }

  /// Create a new category
  Future<bool> createCategory(String name) async {
    final request = CategoryCreateRequest(name: name);
    final result = await _categoryService.createCategory(request);

    return result.when(
      success: (category) {
        state = state.copyWith(categories: [...state.categories, category]);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Update a category
  Future<bool> updateCategory(String categoryId, String newName) async {
    final request = CategoryUpdateRequest(name: newName);
    final result = await _categoryService.updateCategory(categoryId, request);

    return result.when(
      success: (updatedCategory) {
        final updatedCategories = state.categories.map((cat) {
          return cat.id == categoryId ? updatedCategory : cat;
        }).toList();
        state = state.copyWith(categories: updatedCategories);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Delete a category
  Future<bool> deleteCategory(String categoryId) async {
    final result = await _categoryService.deleteCategory(categoryId);

    return result.when(
      success: (_) {
        final updatedCategories = state.categories
            .where((cat) => cat.id != categoryId)
            .toList();
        state = state.copyWith(categories: updatedCategories);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}
