from types import SimpleNamespace
from unittest import TestCase

from src.conf.config_cache import custom_search_key_builder


class TestCacheKeyBuilder( TestCase ):

	def test_custom_search_key_builder( self ):
		user = SimpleNamespace( id=42, )

		def search_function():
			pass

		result = custom_search_key_builder( search_function, namespace="search", args=(), kwargs={ "current_user":
			                                                                                           user,
				}, )

		self.assertEqual( result, "search:search_function:user:42", )
