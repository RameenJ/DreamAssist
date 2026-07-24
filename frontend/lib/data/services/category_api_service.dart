import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/category_model.dart';

/// API service for category-related endpoints
class CategoryApiService {
  final DioClient _dioClient;

  CategoryApiService(this._dioClient);

  /// Get all categories for current user
  Future<Result<List<CategoryModel>>> getCategories() async {
    try {
      final response = await _dioClient.dio.get(AppConfig.categoriesEndpoint);
      
      final List<dynamic> data = response.data as List;
      final categories = data.map((json) => CategoryModel.fromJson(json)).toList();
      
      return Success(categories);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch categories');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Create a new category
  Future<Result<CategoryModel>> createCategory(CategoryCreateRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        AppConfig.categoriesEndpoint,
        data: request.toJson(),
      );
      return Success(CategoryModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to create category');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Update a category
  Future<Result<CategoryModel>> updateCategory(
    String categoryId,
    CategoryUpdateRequest request,
  ) async {
    try {
      final response = await _dioClient.dio.put(
        '${AppConfig.categoriesEndpoint}/$categoryId',
        data: request.toJson(),
      );
      return Success(CategoryModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to update category');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Delete a category
  Future<Result<void>> deleteCategory(String categoryId) async {
    try {
      await _dioClient.dio.delete('${AppConfig.categoriesEndpoint}/$categoryId');
      return const Success(null);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to delete category');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }
}
